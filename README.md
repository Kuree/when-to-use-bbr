# Install

### Setting up Mininet VM
We use the VM recommended by the Mininet (Ubuntu 20.04.1 VM image). You can download the image
[here](https://github.com/mininet/mininet/releases/tag/2.3.0).

### Setting up BBR on Mininet VM
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
