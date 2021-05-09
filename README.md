# Reproducing Network Research
This is our final project for Stanford CS224 for the paper:
[When to use and when not to use BBR: An empirical analysis
and evaluation study](https://www3.cs.stonybrook.edu/~arunab/papers/imc19_bbr.pdf)

## Install

### Setting up Mininet VM
We use the VM recommended by the Mininet (Ubuntu 20.04.1 VM image). You can download the image
[here](https://github.com/mininet/mininet/releases/tag/2.3.0).

### Setting Mininet VM
We need some packages that's not installed by default in the Mininet VM

#### BBR Kernel Module
```bash
sudo apt update
sudo apt install -y linux-generic-hwe-20.04
# need to reboot the VM
sudo reboot
# load the kernel module
sudo modprobe tcp_bbr
# check to see if BBR is available in the kernel
cat /proc/sys/net/ipv4/tcp_available_congestion_control
```

#### iperf3
We use modern `iperf3` instead of `iperf`.

```bash
sudo apt update && sudo apt install -y iperf3
```


### Setting up VM for local unit test
For unit test, we assume you have two Mininet VMs running in your host OS and they can talk
to each other. The easiest way to set up the network is to use `Bridged Adapter` in the
networking option.

In addition, the "remote host" needs to change its `sshd` default permission to allow SSH
tunnelling:

1. Add the following to `/etc/ssh/sshd_config
    ```
    PermitTunnel yes
    ```
2. Then restart the `sshd` service:
    ```
    sudo systemctl restart ssh.service
    ```
