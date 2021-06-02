# Usage: <script> <folder>
# Figure 5
for bs in 0.1 10;
do
  sudo ./run mininet -t 60 -c cubic --size-range ${bs} --loss-range 0 -o $1/figure5/cubic_${bs}
done

# Figure 6
for bs in 0.1 10;
do
  sudo ./run mininet --total-size 100 -c cubic --size-range ${bs} --loss-range 0 -o $1/figure6/cubic_${bs}_100
done

# Figure 5
for bs in 0.1 10;
do
  sudo ./run mininet -t 60 -c bbr --size-range ${bs} --loss-range 0 -o $1/figure5/bbr_${bs}
done

# Figure 6
for bs in 0.1 10;
do
  sudo ./run mininet --total-size 100 -c bbr --size-range ${bs} --loss-range 0 -o $1/figure6/bbr_${bs}_100
done

# Figure 8
sudo ./run mininet -t 60 -c bbr --h2 --h2-cc cubic --size-range 0.01 0.1 1 5 10 50 100 --loss-range 0 --rtt 20 --bw 1000 -o $1/figure8

# Figure 8 run #2
sudo ./run mininet -t 60 -c cubic --h2 --h2-cc bbr --size-range 0.01 0.1 1 5 10 50 100 --loss-range 0 --rtt 20 --bw 1000 -o $1/figure8_run2

# Figure 7
sudo ./run mininet --rtt 25 --size 10 --bw 100 --loss-range 0 0.01 0.02 0.05 0.12 0.18 0.25 0.35 0.45 -o $1/figure7/reno/ -c reno;
sudo ./run mininet --rtt 25 --size 10 --bw 100 --loss-range 0 0.01 0.02 0.05 0.12 0.18 0.25 0.35 0.45 -o $1/figure7/cubic/ -c cubic;
sudo ./run mininet --rtt 25 --size 10 --bw 100 --loss-range 0 0.01 0.02 0.05 0.12 0.18 0.25 0.35 0.45 -o $1/figure7/bbr/ -c bbr;
sudo ./run mininet --rtt 25 --size 10 --bw 100 --loss-range 0 0.01 0.02 0.05 0.12 0.18 0.25 0.35 0.45 -o $1/figure7/bbr_3_2/ -c bbr_3_2;
sudo ./run mininet --rtt 25 --size 10 --bw 100 --loss-range 0 0.01 0.02 0.05 0.12 0.18 0.25 0.35 0.45 -o $1/figure7/bbr_11_10/ -c bbr_11_10;

# Figure 8 run #3
sudo ./run mininet -t 60 -c bbr --h2 --h2-cc cubic --size-range 0.01 0.1 1 5 10 50 100 --loss-range 0 --rtt 20 --bw 1000 -o $1/figure8_run3

