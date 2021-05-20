import argparse
import urllib.request
import tempfile
import os
import subprocess


def get_args():
    parser = argparse.ArgumentParser("Build BBR with different gain value")
    parser.add_argument("-o", "--output", help="Working directory. If not set, a temp dir is used", default="",
                        type=str)
    parser.add_argument("--install", action="store_true", help="When set, install to the kernel as well")
    parser.add_argument("--uninstall", action="store_true", help="When set, uninstall the kernel module")
    parser.add_argument("-g", "--gain", nargs=2, help="BBR gain value in the form of a / b", type=int, required=True)
    return parser.parse_args()


def build_install(gain: float, cwd: str, install: bool, uninstall: bool):
    if not os.path.exists(cwd):
        os.makedirs(cwd, exist_ok=True)
    # download the file
    url = "https://github.com/torvalds/linux/raw/9d31d2338950293ec19d9b095fbaa9030899dcb4/net/ipv4/tcp_bbr.c"
    with urllib.request.urlopen(url) as f:
        html = f.read().decode('utf-8')
    # replace the lines based on gain
    lines = html.split("\n")

    # compute ratio
    a, b = gain
    suffix = f"bbr_{a}_{b}"

    for i in range(len(lines)):
        line = lines[i]
        if "BBR_UNIT * 5 / 4," in line:
            lines[i] = f"BBR_UNIT * {a} / {b},"
        if ".name		= \"bbr\"," in line:
            # replace it with a new name
            lines[i] = f".name		= \"{suffix}\","

    code = "\n".join(lines)
    filename = os.path.join(cwd, f"tcp_{suffix}.c")
    with open(filename, "w+") as f:
        f.write(code)

    # also write the make file
    make = os.path.join(cwd, "Makefile")
    with open(make, "w+") as f:
        f.write(f"obj-m += tcp_{suffix}.o\n")
        f.write("KDIR=/lib/modules/`uname -r`/build\n")
        f.write("default:\n")
        f.write("\t$(MAKE) -C $(KDIR) M=$(shell pwd)\n")

    # build it
    subprocess.check_call("make", cwd=cwd, shell=True)
    filename = os.path.join(cwd, f"tcp_{suffix}.ko")
    filename = os.path.abspath(filename)
    if install:
        # install it
        print("Installing", filename)
        subprocess.check_call(["insmod", filename])
    if uninstall:
        print("Uninstalling", filename)
        subprocess.check_call(["rmmod", filename])


def main():
    configs = get_args()
    if configs.output:
        build_install(configs.gain, configs.output, configs.install, configs.uninstall)
    else:
        with tempfile.TemporaryDirectory() as temp:
            build_install(configs.gain, temp, configs.install, configs.uninstall)


if __name__ == "__main__":
    main()
