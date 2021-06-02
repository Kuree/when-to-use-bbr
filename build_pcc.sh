#!/bin/bash
git clone https://github.com/PCCproject/PCC-Kernel.git /tmp/PCC-Kernel -b vivace
cd /tmp/PCC-Kernel/src
make
sudo insmod tcp_pcc.ko
rm -rf /tmp/PCC-Kernel
