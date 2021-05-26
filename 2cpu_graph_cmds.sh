python3 plot.py heatmap -i 2cpu/bbr_0.1 2cpu/cubic_0.1 -x rtt -y bw -t goodput -o 2cpu/figure5a.pdf
# PCC comparisons
python3 plot.py heatmap -i 2cpu/pcc_0.1 2cpu/cubic_0.1 -x rtt -y bw -t goodput -o 2cpu/figure5a_pcc.pdf
python3 plot.py heatmap -i 2cpu/pcc_0.1 2cpu/bbr_0.1 -x rtt -y bw -t goodput -o 2cpu/figure5a_pcc_bbr.pdf

python3 plot.py heatmap -i 2cpu/bbr_10 2cpu/cubic_10 -x rtt -y bw -t goodput -o 2cpu/figure5b.pdf
# PCC comparisons
python3 plot.py heatmap -i 2cpu/pcc_10 2cpu/cubic_10 -x rtt -y bw -t goodput -o 2cpu/figure5b_pcc.pdf
python3 plot.py heatmap -i 2cpu/pcc_10 2cpu/bbr_10 -x rtt -y bw -t goodput -o 2cpu/figure5b_pcc_bbr.pdf

python3 plot.py heatmap -i 2cpu/bbr_0.1 -x rtt -y bw -t retransmits -o 2cpu/figure5c.pdf
# PCC comparisons
python3 plot.py heatmap -i 2cpu/pcc_0.1 -x rtt -y bw -t retransmits -o 2cpu/figure5cd_pcc.pdf

python3 plot.py heatmap -i 2cpu/cubic_0.1 -x rtt -y bw -t retransmits -o 2cpu/figure5d.pdf

python3 plot.py heatmap -i 2cpu/bbr_0.1_100 2cpu/cubic_0.1_100 -x rtt -y bw -t rtt -o 2cpu/figure6a.pdf
python3 plot.py heatmap -i 2cpu/bbr_10_100 2cpu/cubic_10_100 -x rtt -y bw -t rtt -o 2cpu/figure6b.pdf
# PCC comparisons
python3 plot.py heatmap -i 2cpu/pcc_0.1_100 2cpu/cubic_0.1_100 -x rtt -y bw -t rtt -o 2cpu/figure6a_pcc.pdf
python3 plot.py heatmap -i 2cpu/pcc_10_100 2cpu/cubic_10_100 -x rtt -y bw -t rtt -o 2cpu/figure6b_pcc.pdf
python3 plot.py heatmap -i 2cpu/pcc_0.1_100 2cpu/bbr_0.1_100 -x rtt -y bw -t rtt -o 2cpu/figure6a_pcc_bbr.pdf
python3 plot.py heatmap -i 2cpu/pcc_10_100 2cpu/bbr_10_100 -x rtt -y bw -t rtt -o 2cpu/figure6b_pcc_bbr.pdf

python3 plot.py line -i 2cpu/figure7/bbr 2cpu/figure7/bbr_11_10 2cpu/figure7/bbr_3_2/ 2cpu/figure7/cubic/ 2cpu/figure7/reno 2cpu/figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y goodput -o 2cpu/figure7a.pdf

python3 plot.py line -i 2cpu/figure7/bbr 2cpu/figure7/bbr_11_10 2cpu/figure7/bbr_3_2/ 2cpu/figure7/cubic/ 2cpu/figure7/reno 2cpu/figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y retransmits -o 2cpu/figure7b.pdf

python3 plot.py line -i 2cpu/fairness_bbr/ --split-host -n "BBR" "Cubic" -x buffer_size -y goodput -o 2cpu/figure8a.pdf --add-total --logx
python3 plot.py line -i 2cpu/fairness_pcc/ --split-host -n "PCC" "Cubic" -x buffer_size -y goodput -o 2cpu/figure8a_pcc.pdf --add-total --logx
python3 plot.py line -i 2cpu/fairness_pcc_bbr/ --split-host -n "PCC" "BBR" -x buffer_size -y goodput -o 2cpu/figure8a_pcc_bbr.pdf --add-total --logx
