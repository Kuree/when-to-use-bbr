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

from remote import RemoteHost, RemoteSSHLink, RemoteOVSSwitch


class Topology(mininet.topo.Topo):
    def __init__(self, config):
        self.config = config
        # in Section 3.1, the paper mentioned that the delay between h1/h2 and h3 is 40us
        self._min_delay = "{0}us".format(40 / 2)
        super(Topology, self).__init__()

    def build(self):
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3", server=self.config.remote_host, user=self.config.remote_user,
                          port=self.config.remote_host_port)
        s1 = self.addSwitch("s1")

        # add link
        self.addLink(h1, s1, bw=self.config.bw, delay=self._min_delay)
        self.addLink(h2, s1, bw=self.config.bw, delay=self._min_delay)
        self.addLink(s1, h3, bw=self.config.bw, delay="{0}ms".format(self.config.rtt / 2))


def setup_iperf_server(node, port1, port2):
    # iperf3 only allow one test per server
    cmd1 = f"iperf3 -s -p {port1} -4"
    cmd2 = f"iperf3 -s -p {port2} -4"
    # prevent blocking
    with open(os.devnull, "w") as null:
        node.popen(cmd1, stdout=null, stderr=sys.stderr)
        node.popen(cmd2, stdout=null, stderr=sys.stderr)


def setup_client(node_from: mininet.node.Node, node_to: mininet.node.Node,
                 total_time: float, port: int, cc: str, out: str):
    target_ip = node_to.IP()
    # we output json file
    cmd = f"iperf3 -c {target_ip} -C {cc} -p {port} -w 16m -t {total_time} -i 0 -J --logfile {out} -4"
    node_from.cmd(cmd, shell=True)


def setup_nodes(net: mininet.net.Mininet, configs):
    # hardcode some stuff here
    tcp_port1 = 9998
    tcp_port2 = 9999
    h1 = net.get("h1")
    h2 = net.get("h2")
    h3 = net.get("h3")
    h1_result = os.path.join(configs.output, "h1.json")
    h2_result = os.path.join(configs.output, "h2.json")
    # need to remove this file if already exists
    for filename in {h1_result, h2_result}:
        if os.path.exists(filename):
            os.remove(filename)
    h3_proc = multiprocessing.Process(target=setup_iperf_server, args=(h3, tcp_port1, tcp_port2))
    h1_proc = multiprocessing.Process(target=setup_client, args=(h1, h3, configs.time, tcp_port1, configs.cc,
                                                                 h1_result))
    h2_proc = multiprocessing.Process(target=setup_client, args=(h2, h3, configs.time, tcp_port2, configs.cc,
                                                                 h2_result))

    h3_proc.start()
    time.sleep(0.5)
    h1_proc.start()
    h2_proc.start()

    processes = [h3_proc, h1_proc, h2_proc]
    return processes


def cleanup(processes):
    h3_proc, h1_proc, h2_proc = processes
    for p in {h1_proc, h2_proc}:
        p.join()
    h3_proc.kill()
    mininet.clean.cleanup()


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
    cleanup(processes)


def main():
    parser = argparse.ArgumentParser("BBR experiments")
    parser.add_argument("-c", "--congestion-control", choices=["bbr", "cubic"], default="bbr",
                        help="h1 and h2 congestion control algorithm type", type=str, dest="cc")
    parser.add_argument("--rtt", choices=[5, 10, 25, 50, 75, 100, 150, 200], default=5,
                        help="RTT for the bottle net link", type=int, dest="rtt")
    parser.add_argument("--bw", choices=[10, 20, 50, 100, 250, 500, 1000], default=10,
                        help="Bandwidth for the bottleneck link", type=int, dest="bw")
    parser.add_argument("-s", "--size", "--buffer-size", choices=[0.1, 1, 10, 20, 50], default=0.1,
                        help="Switch buffer size", type=float, dest="size")
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
    args = parser.parse_args()

    # run the experiments
    run(args)


if __name__ == "__main__":
    main()
