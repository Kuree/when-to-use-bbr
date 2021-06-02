sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 2147483647'
sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 2147483647'
sudo sysctl -w net.ipv4.tcp_no_metrics_save=1
sudo sysctl -w net.ipv4.route.flush=1
sudo modprobe tcp_bbr
./build_pcc.sh
sudo python3 build_bbr.py -g 3 2 -o bbr_3_2 --install
sudo python3 build_bbr.py -g 11 10 -o bbr_11_10 --install
