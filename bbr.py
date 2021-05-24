import argparse
import time

import mininet.topo
import mininet.net
import mininet.node
import mininet.link
import mininet.net
import mininet.util
import mininet.clean
import mininet.log
import os
import multiprocessing
import sys
import subprocess
import math

from remote import RemoteHost, RemoteSSHLink, RemoteOVSSwitch
from util import get_iperf_metrics, get_filename, get_available_cc

# MTU - 40 bytes of TCP header size
PACKET_SIZE = 1500 - 40


def get_queue_size(buffer_size):
    return int(math.ceil(buffer_size * 1000 * 1000 / PACKET_SIZE))


class Topology(mininet.topo.Topo):
    def __init__(self, config):
        self.config = config
        # in Section 3.1, the paper mentioned that the delay between h1/h2 and h3 is 40us
        self._min_delay = "{0}us".format(40 / 2)
        super(Topology, self).__init__()

    def build(self):
        # we don't use namespace since it removes the kernel count for tcp transmission
        h1 = self.addHost("h1", inNamespace=False)
        h3 = self.addHost("h3", server=self.config.remote_host, user=self.config.remote_user,
                          port=self.config.remote_host_port, inNamespace=True)
        s1 = self.addSwitch("s1")
        # [3.1] Host links have 1Gbps peak BW.
        self.addLink(h1, s1, bw=1000, delay=self._min_delay)
        # keyi: need to convert to number of bytes, then divided by the MTU to obtain number of packets
        # mininet does the following parameter passing to tc:
        # 'limit %d' % max_queue_size if max_queue_size is not None
        # which produces the following command (e.g.)
        # tc qdisc add dev s1-eth2  parent 5:1  handle 10: netem delay 75.0ms limit XX
        # based on man tc-netem, limit is specified by the number of packets, hence we need
        # to do a conversion
        self.addLink(s1, h3, bw=self.config.bw, delay="{0}ms".format(self.config.rtt / 2),
                     loss=(self.config.loss * 100) if self.config.loss > 0 else None,
                     max_queue_size=get_queue_size(self.config.buffer_size))

        if self.config.h2:
            h2 = self.addHost("h2", inNamespace=False)
            self.addLink(h2, s1, bw=1000, delay=self._min_delay)

    def get_senders(self):
        if self.config.h2:
            return ["h1", "h2"]
        else:
            return ["h1"]


def get_iperf3_server_commands(port1, port2):
    # iperf3 only allow one test per server
    cmd1 = f"iperf3 -s -p {port1} -4"
    cmd2 = f"iperf3 -s -p {port2} -4"
    return cmd1, cmd2


def setup_mininet_iperf_server(node, port1, port2, configs):
    cmd1, cmd2 = get_iperf3_server_commands(port1, port2)
    # prevent blocking
    if configs.debug:
        print(node.name + ":", cmd1)
        node.popen(cmd1, stdout=sys.stdout, stderr=sys.stderr)
    else:
        node.popen(cmd1, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if port2 is not None:
        if configs.debug:
            print(node.name + ":", cmd2)
            node.popen(cmd2, stdout=sys.stdout, stderr=sys.stderr)
        else:
            node.popen(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def setup_lan_iperf_server(port1, port2, configs):
    # killall the iperf3 server first
    commands = ["ssh", f"mininet@{configs.remote_host}", "-p", f"{configs.remote_host_port}", "killall", "iperf3"]
    subprocess.call(commands, stderr=subprocess.DEVNULL)

    cmd1, cmd2 = get_iperf3_server_commands(port1, port2)

    processes = []
    commands = [cmd1, cmd2] if port2 is not None else [cmd1]
    for cmd in commands:
        if configs.debug:
            # need to ssh to the host and run that command
            commands = ["ssh", f"mininet@{configs.remote_host}", "-p", f"{configs.remote_host_port}"] + cmd.split()
            print(configs.remote_host + ":", " ".join(commands))
            p = subprocess.Popen(commands, stdout=sys.stdout, stderr=sys.stderr)
        else:
            p = subprocess.Popen(commands, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        processes.append(p)
    return processes


def get_iperf3_client_cmd(target_ip, port, filename, configs):
    # we output json file
    # mtu 1500
    # no delay
    # window 16Mb
    args = ["iperf3", "-c", f"{target_ip}", "-C", f"{configs.cc}", f"-p {port}",
            "-N", "-M", f"{PACKET_SIZE}",  "-i", "0", "-J", "-4", "--logfile", f"{filename}"]
    if configs.total_size > 0:
        args += ["-n", f"{configs.total_size}M"]
    else:
        args += ["-t", f"{configs.time}"]
    # ignore the slow start, which is approximately 1s
    args += ["-O", "1"]
    if configs.remote_host == "localhost":
        args += ["--window", "16M"]
    return args


def setup_client(node_from: mininet.node.Node, node_to: mininet.node.Node, configs, port, filename):
    target_ip = node_to.IP()
    # we output json file
    # mtu 1500
    # no delay
    # window 16Mb
    args = get_iperf3_client_cmd(target_ip, port, filename, configs)
    cmd = " ".join(args)
    if configs.debug:
        print(node_from.name + ":", cmd)
    node_from.cmd(cmd, shell=True, stderr=sys.stderr)


def setup_nodes(net: mininet.net.Mininet, configs):
    # hardcode some stuff here
    tcp_port1 = 9998
    tcp_port2 = 9999 if configs.h2 else None
    h1 = net.get("h1")
    h3 = net.get("h3")
    h1_result = get_filename(h1, configs)
    h2_result = get_filename("h2", configs)
    # need to remove this file if already exists
    for filename in {h1_result, h2_result}:
        if os.path.exists(filename):
            os.remove(filename)
    h3_proc = multiprocessing.Process(target=setup_mininet_iperf_server, args=(h3, tcp_port1, tcp_port2, configs))
    h1_proc = multiprocessing.Process(target=setup_client, args=(h1, h3, configs, tcp_port1, h1_result))
    if configs.h2:
        h2 = net.get("h2")
        h2_proc = multiprocessing.Process(target=setup_client, args=(h2, h3, configs, tcp_port2, h2_result))
    else:
        h2_proc = None

    h3_proc.start()
    time.sleep(0.5)
    h1_proc.start()
    if configs.h2:
        h2_proc.start()

    processes = [h3_proc, h1_proc, h2_proc]
    return processes


def setup_lan(configs):
    # we directly use iperf3 and tc, since mininet remote is not working properly
    tcp_port1 = 9998
    tcp_port2 = 9999 if configs.h2 else None
    h1_result = get_filename("h1", configs)
    h2_result = get_filename("h2", configs)
    # need to remove this file if already exists
    for filename in {h1_result, h2_result}:
        if os.path.exists(filename):
            os.remove(filename)

    h1_commands = get_iperf3_client_cmd(configs.remote_host, tcp_port1, h1_result, configs)
    h2_commands = get_iperf3_client_cmd(configs.remote_host, tcp_port2, h2_result, configs)

    # start the server
    processes = [setup_lan_iperf_server(tcp_port1, tcp_port2, configs)]

    # set up tc command
    tc_cmd = ["tc", "qdisc", "add", "dev", "eth0", "root", "netem"]
    # add delay
    tc_cmd += ["delay", f"{configs.rtt / 2}ms"]
    # add buffer size
    tc_cmd += ["limit", f"{get_queue_size(configs.buffer_size)}"]
    # bandwidth
    tc_cmd += ["rate", f"{configs.bw}Mbit"]
    if configs.loss > 0:
        tc_cmd += ["loss", f"{int(configs.loss * 100)}%"]
    if configs.debug:
        print("tc:", " ".join(tc_cmd))
    subprocess.check_call(tc_cmd)
    # sleep a little bit to make sure the server is running
    time.sleep(1)

    # run the clients
    if configs.debug:
        print("h1", " ".join(h1_commands))
    p = subprocess.Popen(h1_commands, stderr=sys.stderr, stdout=sys.stdout)
    processes.append(p)
    if tcp_port2 is not None:
        p = subprocess.Popen(h2_commands, stderr=sys.stderr, stdout=sys.stdout)
        processes.append(p)
    else:
        processes.append(None)

    return processes


def cleanup_mininet(net: mininet.net.Mininet, processes):
    h3_proc, h1_proc, h2_proc = processes
    for p in {h1_proc, h2_proc}:
        if p is not None:
            p.join()
    h3_proc.kill()
    h3 = net.get("h3")
    # killall iperf3 instances
    h3.cmd("killall iperf3")
    mininet.clean.cleanup()


def clear_lan_iperf3(debug):
    cmd = "sudo tc qdisc del dev eth0 root netem"
    if debug:
        print("tc:", cmd)
    subprocess.call(cmd.split(), stderr=subprocess.DEVNULL)


def cleanup_lan(processes, debug):
    h3_processes, h1_proc, h2_proc = processes
    for p in {h1_proc, h2_proc}:
        if p is not None:
            while True:
                poll = p.poll()
                if poll is None:
                    time.sleep(0.1)
                else:
                    break
    for p in h3_processes:
        p.kill()
    clear_lan_iperf3(debug)


def check_output(configs):
    # check if we generate the outputs properly
    h1_result = get_filename("h1", configs)
    h2_result = get_filename("h2", configs)
    results = [h1_result]
    if configs.h2:
        results.append(h2_result)
    for filename in results:
        get_iperf_metrics(filename)


def run(configs):
    # if output directory doesn't exist, create them
    if not os.path.exists(configs.output):
        os.makedirs(configs.output, exist_ok=True)

    if configs.mininet_debug:
        mininet.log.setLogLevel("debug")
    if configs.remote_host != "localhost":
        # use bare-metal iperf3 and tc
        clear_lan_iperf3(configs.debug)
        processes = setup_lan(configs)
        cleanup_lan(processes, configs.debug)
    else:
        # clean up previous mininet runs in case of crashes
        mininet.clean.cleanup()
        topology = Topology(configs)
        net = mininet.net.Mininet(topology, host=mininet.node.CPULimitedHost, link=mininet.link.TCLink)
        net.start()

        if configs.debug:
            # test out the component
            mininet.util.dumpNetConnections(net)
            net.pingAll()

        processes = setup_nodes(net, configs)
        if configs.mininet_debug:
            mininet.log.setLogLevel("error")

        # clean up at the end
        cleanup_mininet(net, processes)
    # check if we got everything
    check_output(configs)


def main():
    parser = argparse.ArgumentParser("BBR experiments")
    ccs = get_available_cc()
    parser.add_argument("-c", "--congestion-control", choices=ccs, default="bbr",
                        help="h1 congestion control algorithm type", type=str, dest="cc")
    parser.add_argument("--rtt", choices=[5, 10, 25, 50, 75, 100, 150, 200], default=5,
                        help="RTT for the bottle net link", type=int, dest="rtt")
    parser.add_argument("--bw", choices=[10, 20, 50, 100, 250, 500, 750, 1000], default=10,
                        help="Bandwidth for the bottleneck link", type=int, dest="bw")
    parser.add_argument("-s", "--size", "--buffer-size", choices=[0.1, 1, 10, 20, 50], default=0.1,
                        help="Switch buffer size", type=float,
                        dest="buffer_size")
    parser.add_argument("--remote-host", default="localhost", type=str, dest="remote_host",
                        help="remote host name/IP address")
    parser.add_argument("--remote-host-port", default=22, type=int, dest="remote_host_port",
                        help="remote host port number to ssh in")
    parser.add_argument("--remote-user", default="", type=str, dest="remote_user",
                        help="remote host user name")
    parser.add_argument("-t", "--time", default=60, type=int, help="How long should the experiment run",
                        dest="time")
    parser.add_argument("--total-size", default=0, type=int, help="Total number of bytes to send (in MB). Cannot be "
                                                                  "used together with time", dest="total_size")
    parser.add_argument("--debug", action="store_true", dest="debug")
    parser.add_argument("-o", "--output", type=str, dest="output", help="Output directory for the experiment",
                        default="out")
    parser.add_argument("-l", "--loss", type=float, default=0, dest="loss", help="Link loss rate")
    # whether to add h2
    parser.add_argument("--h2", action="store_true", dest="h2", help="Whether to use h2 in the experiment")
    parser.add_argument("--h2-cc", default="bbr", choices=ccs,
                        help="h1 congestion control algorithm type", type=str, dest="h2_cc")
    # for mininet debug
    parser.add_argument("--mininet-debug", action="store_true", dest="mininet_debug")
    args = parser.parse_args()

    # run the experiments
    run(args)


if __name__ == "__main__":
    main()
