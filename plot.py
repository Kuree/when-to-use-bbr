import matplotlib
import argparse
import seaborn
import pandas as pd
import numpy as np
from util import get_all_metrics, parse_name_config, config_param_names

commands = ["heatmap"]


def get_configs():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", description="Plot iperf graph", required=True)
    for command in commands:
        p = subparsers.add_parser(command)
        p.add_argument("-o", "--out", dest="out", help="Output file", required=True)
        p.add_argument("-i", "--input", nargs="+", dest="input", help="Input directory", required=True)

        if command == "heatmap":
            p.add_argument("-x", help="X axis param name", required=True, dest="x")
            p.add_argument("-y", help="Y axis param name", required=True, dest="y")
            p.add_argument("-t", "--target", choices=["goodput", "rtt", "retransmits"], required=True,
                           help="Target measurement", dest="target")

    return parser.parse_args()


def compute_gain(mat1, mat2):
    # in this case mat1 is bbr and mat2 is cubic
    return np.divide(np.subtract(mat1, mat2), mat2)


def get_heatmap_dataframe(mat, x_values, y_values, names):
    result = []
    for y in range(len(y_values)):
        for x in range(len(x_values)):
            result.append((x_values[x], y_values[y], mat[y][x]))

    return pd.DataFrame(result, columns=names)


def plot_heatmap(configs):
    assert len(configs.input) == 2
    # load stats from two directories
    stats1 = get_all_metrics(configs.input[0])
    stats2 = get_all_metrics(configs.input[1])
    # make sure we have the same stuff
    assert len(stats1) > 0
    assert len(stats1) == len(stats2)
    for name in stats1:
        assert name in stats2
    # based on the names, figure out which two variables to use
    params = [(parse_name_config(name), name) for name in stats1]
    param_values = {}
    for param, name in params:
        for param_name in config_param_names:
            if param_name not in param_values:
                param_values[param_name] = set()
            param_values[param_name].add(getattr(param, param_name))
    # make sure the x and y is correct
    for param_name in config_param_names:
        if param_name in {configs.x, configs.y}:
            assert len(param_values[param_name]) > 1
        else:
            assert len(param_values[param_name]) == 1

    # compute value matrix
    x_values = list(param_values[configs.x])
    y_values = list(param_values[configs.y])
    x_values.sort()
    y_values.sort()
    mat1 = np.zeros(shape=(len(y_values), len(x_values)), dtype=np.float64)
    mat2 = np.zeros(shape=(len(y_values), len(x_values)), dtype=np.float64)

    for y, y_value in enumerate(y_values):
        for x, x_value in enumerate(x_values):
            # find the value
            met1 = None
            met2 = None
            for param, name in params:
                if getattr(param, configs.x) == x_value and getattr(param, configs.y) == y_value:
                    # found it
                    met1 = stats1[name]
                    met2 = stats2[name]
            assert met1 is not None, "Unable to construct matrix"
            if configs.target == "goodput":
                mat1[y][x] = met1[0]
                mat2[y][x] = met2[0]
            elif configs.target == "rtt":
                mat1[y][x] = met1[1]
                mat2[y][x] = met2[1]
            elif configs.target == "retransmits":
                mat1[y][x] = met1[2]
                mat2[y][x] = met2[2]

    gain = compute_gain(mat1 + mat1, mat2)
    # prepare panda dataframe

    df = get_heatmap_dataframe(gain, x_values, y_values, [configs.y, configs.x, "value"])
    df = df.pivot(configs.y, configs.x, "value")
    ax = seaborn.heatmap(df)
    # set labels if necessary
    if configs.x == "rtt":
        ax.set_xlabel("RTT (ms)")
    if configs.y == "bw":
        ax.set_ylabel("Bandwidth (Mbps)")

    fig = ax.get_figure()
    fig.savefig(configs.out)


def main():
    matplotlib.use('Agg')
    configs = get_configs()
    if configs.command == "heatmap":
        plot_heatmap(configs)


if __name__ == "__main__":
    main()
