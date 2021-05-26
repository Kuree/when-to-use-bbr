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
        max_queue_size = int(math.ceil(self.config.buffer_size * 1000 * 1000 / PACKET_SIZE))
        if self.config.debug:
            print(f"max_queue_size: {max_queue_size}")
        self.addLink(s1, h3, bw=self.config.bw, delay="{0}ms".format(self.config.rtt / 2),
                     loss=(self.config.loss * 100) if self.config.loss > 0 else None,
                     max_queue_size=max_queue_size,
                     use_tbf=True)

        if self.config.h2:
            h2 = self.addHost("h2", inNamespace=False)
            self.addLink(h2, s1, bw=1000, delay=self._min_delay)

    def get_senders(self):
        if self.config.h2:
            return ["h1", "h2"]
        else:
            return ["h1"]


def setup_iperf_server(node, port1, port2, configs):
    # iperf3 only allow one test per server
    cmd1 = f"iperf3 -s -p {port1} -4"
    cmd2 = f"iperf3 -s -p {port2} -4"
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


def setup_client(node_from: mininet.node.Node, node_to: mininet.node.Node,
                 configs, port, filename, cc):
    target_ip = node_to.IP()
    # we output json file
    # mtu 1500
    # no delay
    # window 16Mb
    args = ["sudo iperf3", "-c", f"{target_ip}", "-C", f"{cc}", f"-p {port}",
            "-N", f"-M {PACKET_SIZE}",  "-i 0 -J -4", f"--logfile {filename}"]
    if configs.total_size > 0:
        args += [f"-n {configs.total_size}M"]
    else:
        args += [f"-t {configs.time}"]
    # ignore the slow start, which is approximately 1s
    args += ["-O 1"]
    # if not remote host, ignore the window since iperf3 complains about it
    if configs.remote_host == "localhost":
        args += ["--window 16M"]
    cmd = " ".join(args)
    if configs.debug:
        print(f"setup_client: {node_from.name}: {cmd}")
    node_from.cmd(cmd, shell=True, stderr=sys.stderr, stdout=sys.stdout)


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
    h3_proc = multiprocessing.Process(target=setup_iperf_server, args=(h3, tcp_port1, tcp_port2, configs))
    h1_proc = multiprocessing.Process(target=setup_client,
                                      args=(h1, h3, configs, tcp_port1, h1_result, configs.cc))
    if configs.h2:
        h2 = net.get("h2")
        h2_proc = multiprocessing.Process(target=setup_client,
                                          args=(h2, h3, configs, tcp_port2, h2_result, configs.h2_cc))
    else:
        h2_proc = None

    h3_proc.start()
    time.sleep(2 if configs.h2 else 0.5)
    h1_proc.start()
    if configs.h2:
        h2_proc.start()

    processes = [h3_proc, h1_proc, h2_proc]
    return processes


def cleanup(net: mininet.net.Mininet, processes):
    h3_proc, h1_proc, h2_proc = processes
    for p in {h1_proc, h2_proc}:
        if p is not None:
            p.join()
    h3_proc.kill()
    h3 = net.get("h3")
    # killall iperf3 instances
    h3.cmd("killall iperf3")
    mininet.clean.cleanup()


def check_output(topology: Topology, configs):
    # check if we generate the outputs properly
    nodes = topology.get_senders()
    for node in nodes:
        filename = get_filename(node, configs)
        get_iperf_metrics(filename)


def run(configs):
    # clean up previous mininet runs in case of crashes
    mininet.clean.cleanup()
    # if output directory doesn't exist, create them
    if not os.path.exists(configs.output):
        os.makedirs(configs.output, exist_ok=True)

    topology = Topology(configs)
    if configs.mininet_debug:
        mininet.log.setLogLevel("debug")
    if configs.remote_host != "localhost":
        net = mininet.net.Mininet(topology, host=RemoteHost, link=RemoteSSHLink, switch=RemoteOVSSwitch,
                                  waitConnected=True)
    else:
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
    cleanup(net, processes)
    # check if we got everything
    check_output(topology, configs)


def main():
    parser = argparse.ArgumentParser("BBR experiments")
    ccs = get_available_cc()
    parser.add_argument("-c", "--congestion-control", choices=ccs, default="bbr",
                        help="h1 congestion control algorithm type", type=str, dest="cc")
    parser.add_argument("--rtt", choices=[5, 10, 20, 25, 50, 75, 100, 150, 200], default=5,
                        help="RTT for the bottle net link", type=int, dest="rtt")
    parser.add_argument("--bw", choices=[10, 20, 50, 100, 250, 500, 750, 1000], default=10,
                        help="Bandwidth for the bottleneck link", type=int, dest="bw")
    parser.add_argument("-s", "--size", "--buffer-size", choices=[0.01, 0.1, 0.5, 1, 5, 10, 20, 50, 100], default=0.1,
                        help="Switch buffer size in MB", type=float,
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
