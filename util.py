# utilities functions

import json
import sys
import os
import collections


def get_iperf_metrics(filename):
    with open(filename) as f:
        data = json.load(f)
    # we only need to end
    end = data["end"]
    if "sum_sent" not in end:
        print(f"Unable to find final stats for {filename}!", file=sys.stderr)
        return 0, 0, 0
    sum_sent = end["sum_sent"]
    retransmits = sum_sent["retransmits"]
    sum_received = end["sum_received"]
    # this is the receiver's information
    goodput = sum_received["bits_per_second"]
    # need to get mean RTT as well, which is the latency
    stream = end["streams"][0]  # only one stream
    sender = stream["sender"]
    mean_rtt = sum_received["seconds"]
    return goodput, mean_rtt, retransmits


def get_all_metrics(dirname, split_host=False):
    json_files = [os.path.join(dirname, fn) for fn in os.listdir(dirname) if fn.endswith(".json")]
    if split_host:
        result = {}
        for filename in json_files:
            fn = os.path.basename(filename)
            name = os.path.splitext(fn)[0]
            host = name.split("-")[0]
            if host not in result:
                result[host] = {}
            metric = get_iperf_metrics(filename)
            result[host][name] = metric
        array_result = []
        keys = list(result.keys())
        keys.sort()
        for host in keys:
            array_result.append(result[host])
        return array_result
    else:
        result = {}
        for filename in json_files:
            fn = os.path.basename(filename)
            name = os.path.splitext(fn)[0]
            metric = get_iperf_metrics(filename)
            result[name] = metric
        return result


config_param_names = ["hostname", "buffer_size", "rtt", "bw", "loss"]
ExperimentConfig = collections.namedtuple("ExperimentConfig", config_param_names)


def parse_name_config(name):
    tokens = name.split("-")
    hostname = tokens[0]
    buffer_token = tokens[1]
    assert buffer_token[0] == "b"
    buffer_size = float(buffer_token[1:])
    rtt_token = tokens[2]
    assert rtt_token[:3] == "rtt"
    rtt = int(rtt_token[3:])
    bw_token = tokens[3]
    assert bw_token[:2] == "bw"
    bw = int(bw_token[2:])
    loss_token = tokens[4]
    assert loss_token[0] == "l"
    loss = float(loss_token[1:])
    return ExperimentConfig(hostname=hostname, buffer_size=buffer_size, rtt=rtt, bw=bw, loss=loss)


def get_filename(node, configs):
    name = node if isinstance(node, str) else node.name
    buffer_size = configs.buffer_size
    rtt = configs.rtt
    bw = configs.bw
    loss = configs.loss
    return os.path.join(configs.output, f"{name}-b{buffer_size}-rtt{rtt}-bw{bw}-l{loss}.json")


def get_available_cc():
    with open("/proc/sys/net/ipv4/tcp_available_congestion_control") as f:
        values = f.read()
    return values.split()


def __main():
    if len(sys.argv) == 2:
        if sys.argv[1].endswith(".json"):
            goodput, mean_rtt, retransmits = get_iperf_metrics(sys.argv[1])
            print(f"Goodput: {goodput} Mean RTT: {mean_rtt} Retr: {retransmits}")
        else:
            data = get_all_metrics(sys.argv[1])
            assert len(data) > 0, f"{sys.argv[1]} empty!"
            for name, metric in data.items():
                config = parse_name_config(name)
                goodput, mean_rtt, retransmits = metric
                print(config, f"Goodput: {goodput} Mean RTT: {mean_rtt} Retr: {retransmits}")


if __name__ == "__main__":
    __main()
