#!/usr/bin/env bash

set -xe
echo "net.ipv4.tcp_no_metrics_save=1" | sudo tee -a /etc/sysctl.conf
echo "net.ipv4.tcp_mem=1024087380268435456" | sudo tee -a /etc/sysctl.conf
# apply the changes now
sudo sysctl -p
