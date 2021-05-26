python3 plot.py heatmap -i bbr_0.1 cubic_0.1 -x rtt -y bw -t goodput -o figure5a.pdf
# PCC comparisons
python3 plot.py heatmap -i pcc_0.1 cubic_0.1 -x rtt -y bw -t goodput -o figure5a_pcc.pdf
python3 plot.py heatmap -i pcc_0.1 bbr_0.1 -x rtt -y bw -t goodput -o figure5a_pcc_bbr.pdf

python3 plot.py heatmap -i bbr_10 cubic_10 -x rtt -y bw -t goodput -o figure5b.pdf
# PCC comparisons
python3 plot.py heatmap -i pcc_10 cubic_10 -x rtt -y bw -t goodput -o figure5b_pcc.pdf
python3 plot.py heatmap -i pcc_10 bbr_10 -x rtt -y bw -t goodput -o figure5b_pcc_bbr.pdf

python3 plot.py heatmap -i bbr_0.1 -x rtt -y bw -t retransmits -o figure5c.pdf
# PCC comparisons
python3 plot.py heatmap -i pcc_0.1 -x rtt -y bw -t retransmits -o figure5cd_pcc.pdf

python3 plot.py heatmap -i cubic_0.1 -x rtt -y bw -t retransmits -o figure5d.pdf

python3 plot.py heatmap -i bbr_0.1_100 cubic_0.1_100 -x rtt -y bw -t rtt -o figure6a.pdf
python3 plot.py heatmap -i bbr_10_100 cubic_10_100 -x rtt -y bw -t rtt -o figure6b.pdf
# PCC comparisons
python3 plot.py heatmap -i pcc_0.1_100 cubic_0.1_100 -x rtt -y bw -t rtt -o figure6a_pcc.pdf
python3 plot.py heatmap -i pcc_10_100 cubic_10_100 -x rtt -y bw -t rtt -o figure6b_pcc.pdf
python3 plot.py heatmap -i pcc_0.1_100 bbr_0.1_100 -x rtt -y bw -t rtt -o figure6a_pcc_bbr.pdf
python3 plot.py heatmap -i pcc_10_100 bbr_10_100 -x rtt -y bw -t rtt -o figure6b_pcc_bbr.pdf

python3 plot.py line -i figure7/bbr figure7/bbr_11_10 figure7/bbr_3_2/ figure7/cubic/ figure7/reno figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y goodput -o figure7a.pdf

python3 plot.py line -i figure7/bbr figure7/bbr_11_10 figure7/bbr_3_2/ figure7/cubic/ figure7/reno figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y retransmits -o figure7b.pdf

python3 plot.py line -i fairness_bbr/ --split-host -n "BBR" "Cubic" -x buffer_size -y goodput -o figure8a.pdf --add-total --logx
python3 plot.py line -i fairness_pcc/ --split-host -n "PCC" "Cubic" -x buffer_size -y goodput -o figure8a_pcc.pdf --add-total --logx
python3 plot.py line -i fairness_pcc_bbr/ --split-host -n "PCC" "BBR" -x buffer_size -y goodput -o figure8a_pcc_bbr.pdf --add-total --logx
