# utilities functions

import json
import sys


def get_iperf_metrics(filename):
    with open(filename) as f:
        data = json.load(f)
    # we only need to end
    end = data["end"]
    sum_sent = end["sum_sent"]
    retransmits = sum_sent["retransmits"]
    sum_received = end["sum_received"]
    # this is the receiver's information
    goodput = sum_received["bits_per_second"]
    # need to get mean RTT as well, which is the latency
    stream = end["streams"][0]  # only one stream
    sender = stream["sender"]
    mean_rtt = sender["mean_rtt"]
    return goodput, mean_rtt, retransmits


def __main():
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        goodput, mean_rtt, retransmits = get_iperf_metrics(sys.argv[1])
        print(f"Goodput: {goodput} Mean RTT: {mean_rtt} Retr: {retransmits}")


if __name__ == "__main__":
    __main()
