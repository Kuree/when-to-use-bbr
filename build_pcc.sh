#!/bin/bash
git clone https://github.com/PCCproject/PCC-Kernel.git /tmp
cd /tmp/PCC-Kernel/src
make
sudo insmod tcp_pcc.ko
