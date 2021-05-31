# Reproducing Network Research
This is our final project for Stanford CS224 for the paper:
[When to use and when not to use BBR: An empirical analysis
and evaluation study](https://www3.cs.stonybrook.edu/~arunab/papers/imc19_bbr.pdf)

## Install

### Setting up Mininet VM
We use the VM recommended by the Mininet (Ubuntu 20.04.1 VM image). You can download the image
[here](https://github.com/mininet/mininet/releases/tag/2.3.0).

After you turn up the image, you'll need to download some packages that's not
installed by default in the Mininet VM.

#### BBR Kernel Module
```bash
sudo apt update
sudo apt install -y linux-generic-hwe-20.04
# load the kernel module
sudo modprobe tcp_bbr
# check to see if BBR is available in the kernel
cat /proc/sys/net/ipv4/tcp_available_congestion_control
```

#### PCC Kernel Module
```bash
./build_pcc.sh
# check to see if PCC is available in the kernel
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

1. Add the following to `/etc/ssh/sshd_config`
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
    for cc in bbr cubic pcc;
    do
      sudo ./run mininet -t 60 -c ${cc} --size-range ${bs} --loss-range 0 -o ${cc}_${bs}
    done
  done
  ```

  Then we can use `plot.py` to create desired heatmap:

  - a:
    
    ```bash
      python3 plot.py heatmap -i bbr_0.1 cubic_0.1 -x rtt -y bw -t goodput -o figure5a.pdf
      # PCC comparisons
      python3 plot.py heatmap -i pcc_0.1 cubic_0.1 -x rtt -y bw -t goodput -o figure5a_pcc.pdf
      python3 plot.py heatmap -i pcc_0.1 bbr_0.1 -x rtt -y bw -t goodput -o figure5a_pcc_bbr.pdf
    ```

  - b:

    ```bash
      python3 plot.py heatmap -i bbr_10 cubic_10 -x rtt -y bw -t goodput -o figure5b.pdf
      # PCC comparisons
      python3 plot.py heatmap -i pcc_10 cubic_10 -x rtt -y bw -t goodput -o figure5b_pcc.pdf
      python3 plot.py heatmap -i pcc_10 bbr_10 -x rtt -y bw -t goodput -o figure5b_pcc_bbr.pdf
    ```

  - c:
     
    ```bash
      python3 plot.py heatmap -i bbr_0.1 -x rtt -y bw -t retransmits -o figure5c.pdf
      # PCC comparisons
      python3 plot.py heatmap -i pcc_0.1 -x rtt -y bw -t retransmits -o figure5cd_pcc.pdf
    ```

  - d:
     
    ```bash
      python3 plot.py heatmap -i cubic_0.1 -x rtt -y bw -t retransmits -o figure5d.pdf
    ```

- Figure 6

  In this experiment, we need to use total flow size (100MB in this case) instead of total time.

  ```bash
  for bs in 0.1 10;
  do
    for cc in bbr cubic pcc;
    do
      sudo ./run mininet --total-size 100 -c ${cc} --size-range ${bs} --loss-range 0 -o ${cc}_${bs}_100
    done
  done
  ```

  To plot the two figures, we can use the following commands:

  ```bash
  python3 plot.py heatmap -i bbr_0.1_100 cubic_0.1_100 -x rtt -y bw -t rtt -o figure6a.pdf
  python3 plot.py heatmap -i bbr_10_100 cubic_10_100 -x rtt -y bw -t rtt -o figure6b.pdf
  # PCC comparisons
  python3 plot.py heatmap -i pcc_0.1_100 cubic_0.1_100 -x rtt -y bw -t rtt -o figure6a_pcc.pdf
  python3 plot.py heatmap -i pcc_10_100 cubic_10_100 -x rtt -y bw -t rtt -o figure6b_pcc.pdf
  python3 plot.py heatmap -i pcc_0.1_100 bbr_0.1_100 -x rtt -y bw -t rtt -o figure6a_pcc_bbr.pdf
  python3 plot.py heatmap -i pcc_10_100 bbr_10_100 -x rtt -y bw -t rtt -o figure6b_pcc_bbr.pdf
  ```

- Figure 7

  To generate the graph for various lines, we need to run the Mininet simulation individually for
  each congestion control algorithm. We also need to install BBR kernel modules with different pacing
  gain. To do so, simply do
  
  ```
  sudo python3 build_bbr.py -g 3 2 -o bbr_3_2 --install
  sudo python3 build_bbr.py -g 11 10 -o bbr_11_10 --install
  ```
  Gain is specified as a fraction, in this case `3/2`, using two integers. `--install` flag allows us
  to install it into the kernel directly. We need to do this for BBR1.1 (`11 10`) and  BBR1.5 (`3 2`)
  
  After installing the kernel modules, we can run the experiment in a loop:

  ```bash
  for cc in bbr bbr_3_2 bbr_11_10 cubic reno pcc;
  do
    sudo ./run mininet --rtt 25 --size 10 --bw 100 --loss-range 0 0.01 0.02 0.05 0.12 0.18 0.25 0.35 0.45 -o figure7/${cc}/ -c ${cc};
  done
  ```

  Once the runs finish, we can then proceed to plot the graph. We can use the
  following commands to obtain Figure 7a and Figure 7b.

  ```bash
    python ./plot.py line -i figure7/bbr figure7/bbr_11_10 figure7/bbr_3_2/ figure7/cubic/ figure7/reno figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y goodput -o figure7a.pdf

    python ./plot.py line -i figure7/bbr figure7/bbr_11_10 figure7/bbr_3_2/ figure7/cubic/ figure7/reno figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y retransmits -o figure7b.pdf
  ```


- Figure 8
   
  Figure 8 is a little bit tricky to generate. It requires a LAN/WAN and we assume you already has it setup

  LAN version:
    
  ```bash
  ./run shared --rtt 20 --bw 1000 --loss-range 0 --size 0.01 0.02 0.04 0.08 0.1 0.5 1 5 10 --switch 10.10.10.1 --h2 10.10.10.4 --remote-host 10.10.1.2 --cc2 cubic -c bbr -o figure8/lan
  ```

  To plot, we can use the following command:
    
  ```bash
  python3 plot.py line -i figure8/lan --split-host -n "BBR" "Cubic" -x buffer_size -y goodput -o figure8c.pdf --add-total --logx
  ```


## Setting up VMs for LAN test

Unfortunately we have observed abnormal throughput result using Mininet. To obtain proper result, we need a VM-based LAN setup.
We can use three VMs, all of which can be cloned from a base machine with randomized MAC addresses. We will use `h1`, `switch`,
and `h3` to refer to three different VMs. We will use internal network to setup the proper connections. Also make sure that
`Promiscuous Mode` is set to `Allow All`.

- `h1`: Internal Network (`intnet-1`)
- `h3`: Internal Network (`intnet-2`)
- `switch`: Internal Network (`intnet-1` and `intnet-2`)

We then need to setup the static address manually by modifying the `/etc/netplan/01-netcfg.yaml` file:

- `h1`:

  ```yaml
  network:
    version: 2
    renderer: networkd
    ethernets:
      eth0:
        dhcp4: no
        address: [10.10.10.2/24]
        gateway4: 10.10.10.1
  ```

- `h3`:
  
  ```yaml
  network:
    version: 2
    renderer: networkd
    ethernets:
      eth0:
        dhcp4: no
        address: [10.10.1.2/24]
        gateway4: 10.10.1.1
  ```

- `switch`:

  ```yaml
  network:
    version: 2
    renderer: networkd
    ethernets:
      eth0:
        dhcp4: no
        addresses: [10.10.10.1/24]
        gateway4: 10.10.10.1
        routes:
          - to: 10.10.1.0/24
            via: 10.10.10.1
            on-link: true
      eth1:
        dhcp4: no
        addresses: [10.10.1.1/24]
        gateway4: 10.10.1.1
        routes:
          - to: 10.10.10.0/24
            via: 10.10.1.1
            on-link: true

  ```

Here we let the two interface of `switch` route to each other, and we will control TCP traffic on `eth1`, which is linked to `h3` to
emulate the switch/router behavior. Notice that we also need to allow IP forwarding, which can be set via

```sh
echo 1 | sudo tee -a /proc/sys/net/ipv4/ip_forward
```

After setting each host's network configuration, we need to pally changes to `netplan`:

```sh
sudo netplan apply
```

## Setting up VM for WAN
We need to make some modification on the routes with `netplan`. Assume your EC2 instance has IP address or `13.14.15.16`, we need to add routes
to our router VM. First we need to add another network interface with the `NAT` type to the VM, which we assume shows up in the VM as `eth3`. You
should change to proper name based on your VM setup.

`switch`:

```yaml
    eth3:
      dhcp4: yes
      routes:
        - to: 13.0.0.0/8
          via: 10.0.2.2
          on-link: true
```

After apply the new netplan, make sure you can reach that EC2 instance either via `ping` or `traceroute`. Next, we need to enable the NAT routing
table:

```bash
sudo iptables -t nat -A POSTROUTING -o eth3 -j MASQUERADE
```

After that, make sure you can ping the EC2 instance from `h1` and `h2`.

To run the experiments, make sure you add `--remote-ssh-key` to the commands, which should point to your EC2 key-pair. We assume you use standard
Ubuntu 20.04 LTS image to create the instance.
