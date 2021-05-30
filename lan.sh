#!/usr/bin/env bash

set -xe

# figure 5
# turn on debug to monitor the progress
./run lan --size-range 0.1 --loss-range 0 --remote-host 10.10.1.2 --switch 10.10.0.1 -o figure5/cubic_0.1 --debug -c cubic
./run lan --size-range 0.1 --loss-range 0 --remote-host 10.10.1.2 --switch 10.10.0.1 -o figure5/bbr_0.1 --debug -c bbr
./run lan --size-range 10 --loss-range 0 --remote-host 10.10.1.2 --switch 10.10.0.1 -o figure5/cubic_10 --debug -c cubic
./run lan --size-range 10 --loss-range 0 --remote-host 10.10.1.2 --switch 10.10.0.1 -o figure5/bbr_10 --debug -c bbr

# figure 6
./run lan --size-range 0.1 --loss-range 0 --total-size 100 --remote-host 10.10.1.2 --switch 10.10.0.1 -o figure6/cubic_0.1 --debug -c cubic
./run lan --size-range 0.1 --loss-range 0 --total-size 100 --remote-host 10.10.1.2 --switch 10.10.0.1 -o figure6/bbr_0.1 --debug -c bbr
./run lan --size-range 10 --loss-range 0 --total-size 100 --remote-host 10.10.1.2 --switch 10.10.0.1 -o figure6/cubic_10 --debug -c cubic
./run lan --size-range 10 --loss-range 0 --total-size 100 --remote-host 10.10.1.2 --switch 10.10.0.1 -o figure6/bbr_10 --debug -c bbr


# figure 8
./run shared --rtt 20 --bw 1000 --loss-range 0 --size 0.01 0.02 0.04 0.08 0.1 0.5 1 5 10 --switch 10.10.10.1 --h2 10.10.10.4 --remote-host 10.10.1.2 --cc2 cubic -c bbr -o figure8/lan
