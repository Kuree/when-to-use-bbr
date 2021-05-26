python3 plot.py heatmap -i 1cpu/bbr_0.1 1cpu/cubic_0.1 -x rtt -y bw -t goodput -o 1cpu/figure5a.pdf
# PCC comparisons
python3 plot.py heatmap -i 1cpu/pcc_0.1 1cpu/cubic_0.1 -x rtt -y bw -t goodput -o 1cpu/figure5a_pcc.pdf
python3 plot.py heatmap -i 1cpu/pcc_0.1 1cpu/bbr_0.1 -x rtt -y bw -t goodput -o 1cpu/figure5a_pcc_bbr.pdf

python3 plot.py heatmap -i 1cpu/bbr_10 1cpu/cubic_10 -x rtt -y bw -t goodput -o 1cpu/figure5b.pdf
# PCC comparisons
python3 plot.py heatmap -i 1cpu/pcc_10 1cpu/cubic_10 -x rtt -y bw -t goodput -o 1cpu/figure5b_pcc.pdf
python3 plot.py heatmap -i 1cpu/pcc_10 1cpu/bbr_10 -x rtt -y bw -t goodput -o 1cpu/figure5b_pcc_bbr.pdf

python3 plot.py heatmap -i 1cpu/bbr_0.1 -x rtt -y bw -t retransmits -o 1cpu/figure5c.pdf
# PCC comparisons
python3 plot.py heatmap -i 1cpu/pcc_0.1 -x rtt -y bw -t retransmits -o 1cpu/figure5cd_pcc.pdf

python3 plot.py heatmap -i 1cpu/cubic_0.1 -x rtt -y bw -t retransmits -o 1cpu/figure5d.pdf

python3 plot.py heatmap -i 1cpu/bbr_0.1_100 1cpu/cubic_0.1_100 -x rtt -y bw -t rtt -o 1cpu/figure6a.pdf
python3 plot.py heatmap -i 1cpu/bbr_10_100 1cpu/cubic_10_100 -x rtt -y bw -t rtt -o 1cpu/figure6b.pdf
# PCC comparisons
python3 plot.py heatmap -i 1cpu/pcc_0.1_100 1cpu/cubic_0.1_100 -x rtt -y bw -t rtt -o 1cpu/figure6a_pcc.pdf
python3 plot.py heatmap -i 1cpu/pcc_10_100 1cpu/cubic_10_100 -x rtt -y bw -t rtt -o 1cpu/figure6b_pcc.pdf
python3 plot.py heatmap -i 1cpu/pcc_0.1_100 1cpu/bbr_0.1_100 -x rtt -y bw -t rtt -o 1cpu/figure6a_pcc_bbr.pdf
python3 plot.py heatmap -i 1cpu/pcc_10_100 1cpu/bbr_10_100 -x rtt -y bw -t rtt -o 1cpu/figure6b_pcc_bbr.pdf

python3 plot.py line -i 1cpu/figure7/bbr 1cpu/figure7/bbr_11_10 1cpu/figure7/bbr_3_2/ 1cpu/figure7/cubic/ 1cpu/figure7/reno 1cpu/figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y goodput -o 1cpu/figure7a.pdf

python3 plot.py line -i 1cpu/figure7/bbr 1cpu/figure7/bbr_11_10 1cpu/figure7/bbr_3_2/ 1cpu/figure7/cubic/ 1cpu/figure7/reno 1cpu/figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y retransmits -o 1cpu/figure7b.pdf

python3 plot.py line -i 1cpu/fairness_bbr/ --split-host -n "BBR" "Cubic" -x buffer_size -y goodput -o 1cpu/figure8a.pdf --add-total --logx
python3 plot.py line -i 1cpu/fairness_pcc/ --split-host -n "PCC" "Cubic" -x buffer_size -y goodput -o 1cpu/figure8a_pcc.pdf --add-total --logx
python3 plot.py line -i 1cpu/fairness_pcc_bbr/ --split-host -n "PCC" "BBR" -x buffer_size -y goodput -o 1cpu/figure8a_pcc_bbr.pdf --add-total --logx
