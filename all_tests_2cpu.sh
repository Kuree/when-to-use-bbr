for bs in 0.1 10;
do
  for cc in bbr cubic pcc;
  do
    sudo ./run mininet -t 60 -c ${cc} --size-range ${bs} --loss-range 0 -o 2cpu/${cc}_${bs}
  done
done

for bs in 0.1 10;
do
  for cc in bbr cubic pcc;
  do
    sudo ./run mininet --total-size 100 -c ${cc} --size-range ${bs} --loss-range 0 -o 2cpu/${cc}_${bs}_100
  done
done

for cc in bbr bbr_3_2 bbr_11_10 cubic reno pcc;
do
  sudo ./run mininet --rtt 25 --size 10 --bw 100 --loss-range 0 0.01 0.02 0.05 0.12 0.18 0.25 0.35 0.45 -o 2cpu/figure7/${cc}/ -c ${cc};
done

sudo ./run mininet -t 60 -c bbr --h2 --h2-cc cubic --size-range 0.01 0.1 1 5 10 50 100 --loss-range 0 --rtt 20 --bw 1000 -o 2cpu/fairness_bbr
sudo ./run mininet -t 60 -c pcc --h2 --h2-cc cubic --size-range 0.01 0.1 1 5 10 50 100 --loss-range 0 --rtt 20 --bw 1000 -o 2cpu/fairness_pcc
sudo ./run mininet -t 60 -c pcc --h2 --h2-cc bbr --size-range 0.01 0.1 1 5 10 50 100 --loss-range 0 --rtt 20 --bw 1000 -o 2cpu/fairness_pcc_bbr
