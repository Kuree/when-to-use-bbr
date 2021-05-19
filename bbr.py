import argparse
import time

import mininet.topo
import mininet.net
import mininet.node
import mininet.link
import mininet.net
import mininet.util
import mininet.clean
import os
import multiprocessing
import sys
import subprocess

from remote import RemoteHost, RemoteSSHLink, RemoteOVSSwitch
from util import get_iperf_metrics, get_filename


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
        self.addLink(s1, h3, bw=self.config.bw, delay="{0}ms".format(self.config.rtt / 2),
                     loss=self.config.loss,
                     max_queue_size=self.config.buffer_size * 1500)

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
    cmd1 = f"iperf3 -s -p {port1} -4 -w 16m"
    cmd2 = f"iperf3 -s -p {port2} -4 -w 16m"
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
                 total_time: float, port: int, cc: str, out: str, debug: bool):
    target_ip = node_to.IP()
    # we output json file
    # mtu 1500
    # no delay
    # window 16Mb
    cmd = f"iperf3 -c {target_ip} -C {cc} -p {port} -t {total_time} --window 16M  -N -M 1500 -i 0 -J --logfile {out} -4"
    if debug:
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
    h3_proc = multiprocessing.Process(target=setup_iperf_server, args=(h3, tcp_port1, tcp_port2, configs))
    h1_proc = multiprocessing.Process(target=setup_client, args=(h1, h3, configs.time, tcp_port1, configs.cc,
                                                                 h1_result, configs.debug))
    if configs.h2:
        h2 = net.get("h2")
        h2_proc = multiprocessing.Process(target=setup_client, args=(h2, h3, configs.time, tcp_port2, configs.h2_cc,
                                                                     h2_result, configs.debug))
    else:
        h2_proc = None

    h3_proc.start()
    time.sleep(0.5)
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
    # clean up at the end
    cleanup(net, processes)
    # check if we got everything
    check_output(topology, configs)


def main():
    parser = argparse.ArgumentParser("BBR experiments")
    parser.add_argument("-c", "--congestion-control", choices=["bbr", "cubic"], default="bbr",
                        help="h1 congestion control algorithm type", type=str, dest="cc")
    parser.add_argument("--rtt", choices=[5, 10, 25, 50, 75, 100, 150, 200], default=5,
                        help="RTT for the bottle net link", type=int, dest="rtt")
    parser.add_argument("--bw", choices=[10, 20, 50, 100, 250, 500, 750, 1000], default=10,
                        help="Bandwidth for the bottleneck link", type=int, dest="bw")
    parser.add_argument("-s", "--size", "--buffer-size", choices=[0.1, 1, 10, 20, 50], default=0.1,
                        help="Switch buffer size", type=float,
                        dest="buffer_size")
    # TODO(liwenbo): should the default be "" instead?
    parser.add_argument("--remote-host", default="localhost", type=str, dest="remote_host",
                        help="remote host name/IP address")
    parser.add_argument("--remote-host-port", default=22, type=int, dest="remote_host_port",
                        help="remote host port number to ssh in")
    parser.add_argument("--remote-user", default="", type=str, dest="remote_user",
                        help="remote host user name")
    parser.add_argument("-t", "--time", default=60, type=int, help="How long should the experiment run",
                        dest="time")
    parser.add_argument("--debug", action="store_true", dest="debug")
    parser.add_argument("-o", "--output", type=str, dest="output", help="Output directory for the experiment",
                        default="out")
    parser.add_argument("-l", "--loss", type=float, default=0, dest="loss", help="Link loss rate")
    # whether to add h2
    parser.add_argument("--h2", action="store_true", dest="h2", help="Whether to use h2 in the experiment")
    parser.add_argument("--h2-cc", default="bbr", choices=["bbr", "cubic"],
                        help="h1 congestion control algorithm type", type=str, dest="h2_cc")
    args = parser.parse_args()

    # run the experiments
    run(args)


if __name__ == "__main__":
    main()
