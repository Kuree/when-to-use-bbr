import argparse
import mininet.topo
import mininet.net
import mininet.node
import mininet.link
import mininet.net
import mininet.util


class Topology(mininet.topo.Topo):
    def __init__(self, config):
        self.config = config
        # in Section 3.1, the paper mentioned that the delay between h1/h2 and h3 is 40us
        self._min_delay = "{0}us".format(40 / 2)
        super(Topology, self).__init__()

    def build(self):
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")
        s1 = self.addSwitch("s1")

        # add link
        self.addLink(h1, s1, bw=self.config.bw, delay=self._min_delay)
        self.addLink(h2, s1, bw=self.config.bw, delay=self._min_delay)
        self.addLink(s1, h3, bw=self.config.bw, delay="{0}ms".format(self.config.rtt / 2))


def run(configs):
    topology = Topology(configs)
    net = mininet.net.Mininet(topology, host=mininet.node.CPULimitedHost, link=mininet.link.TCLink)
    net.start()
    if configs.debug:
        mininet.util.dumpNetConnections(net)


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
    parser.add_argument("--debug", action="store_true",  dest="debug")
    args = parser.parse_args()

    # run the experiments
    run(args)


if __name__ == "__main__":
    main()
