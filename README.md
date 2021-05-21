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


## Figure generation
In this section we will disucss how to obtain the experiments using Mininet locally.

- Figure 5

  We need to generate two dataset with two different buffer size (`bs`).

  ```bash
  for bs in 0.1 10;
  do
    for cc in bbr cubic;
    do
      sudo ./run mininet -t 60 -c ${cc} --size-range ${bs} --loss-range 0 -o ${cc}_${bs}
    done
  done
  ``` 

  Then we can use `plot.py` to create desired heatmap:

  - a:
    
    ```
      python3 plot.py -i bbr_0.1 cubic_0.1 -x rtt -y bw -t goodput -o figure5a.pdf
    ```

  - b:

    ```
      python3 plot.py -i bbr_10 cubic_10 -x rtt -y bw -t goodput -o figure5b.pdf
    ```

  - c:
     
    ```
      python3 plot.py -i bbr_0.1 -x rtt -y bw -t retransmits -o figure5c.pdf
    ```

  - d:
     
    ```
      python3 plot.py -i cubic_0.1 -x rtt -y bw -t retransmits -o figure5d.pdf
    ```

- Figure 7

  To generate the graph for various lines, we need to run the Mininet simulation individually for
  each congestion control algorithm. We also need to install BBR kernel modules with different pacing
  gain. To do so, simply do
  
  ```
  sudo python3 build_bbr.py -g 3 2 -o bbr_3_2 --install
  ```
  Gain is specified as a fraction, in this case `3/2`, using two integers. `--install` flag allows us
  to install it into the kernel directly. We need to do this for BBR1.1 (`11 10`) and  BBR1.5 (`3 2`)
  
  After installing the kernel modules, we can run the experiment in a loop:

  ```bash
  for cc in bbr bbr_3_2 bbr_11_10 cubic reno;
  do
    sudo ./run mininet --rtt 25 --size 10 --bw 100 --loss-range 0 0.01 0.02 0.05 0.12 0.18 0.25 0.35 0.45 -o figure7/${cc}/ -c ${cc};
  done
  ```

  Once the runs finish, we can then proceed to plot the graph. We can use the
  following commands to obtain Figure 7a and Figure 7b.

  ```bash
    python ./plot.py line -i figure7/bbr figure7/bbr_11_10 figure7/bbr_3_2/ figure7/cubic/ figure7/reno -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" -x loss -y goodput -o figure7a.pdf

    python ./plot.py line -i figure7/bbr figure7/bbr_11_10 figure7/bbr_3_2/ figure7/cubic/ figure7/reno -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" -x loss -y retransmits -o figure7b.pdf
  ```
