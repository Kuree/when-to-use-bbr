# Usage: bash graph_cmds.sh <results folder>
DIR=$1
python3 plot.py heatmap -i $DIR/figure5/bbr_0.1 $DIR/figure5/cubic_0.1 -x rtt -y bw -t goodput -o $DIR/figure5/figure5a.pdf
# PCC comparisons
python3 plot.py heatmap -i $DIR/figure5/pcc_0.1 $DIR/figure5/cubic_0.1 -x rtt -y bw -t goodput -o $DIR/figure5/figure5a_pcc.pdf
python3 plot.py heatmap -i $DIR/figure5/pcc_0.1 $DIR/figure5/bbr_0.1 -x rtt -y bw -t goodput -o $DIR/figure5/figure5a_pcc_bbr.pdf

python3 plot.py heatmap -i $DIR/figure5/bbr_10 $DIR/figure5/cubic_10 -x rtt -y bw -t goodput -o $DIR/figure5/figure5b.pdf
# PCC comparisons
python3 plot.py heatmap -i $DIR/figure5/pcc_10 $DIR/figure5/cubic_10 -x rtt -y bw -t goodput -o $DIR/figure5/figure5b_pcc.pdf
python3 plot.py heatmap -i $DIR/figure5/pcc_10 $DIR/figure5/bbr_10 -x rtt -y bw -t goodput -o $DIR/figure5/figure5b_pcc_bbr.pdf

python3 plot.py heatmap -i $DIR/figure5/bbr_0.1 -x rtt -y bw -t retransmits -o $DIR/figure5/figure5c.pdf
# PCC comparisons
python3 plot.py heatmap -i $DIR/figure5/pcc_0.1 -x rtt -y bw -t retransmits -o $DIR/figure5/figure5cd_pcc.pdf

python3 plot.py heatmap -i $DIR/figure5/cubic_0.1 -x rtt -y bw -t retransmits -o $DIR/figure5/figure5d.pdf

python3 plot.py heatmap -i $DIR/figure6/bbr_0.1 $DIR/figure6/cubic_0.1 -x rtt -y bw -t rtt -o $DIR/figure6/figure6a.pdf
python3 plot.py heatmap -i $DIR/figure6/bbr_10 $DIR/figure6/cubic_10 -x rtt -y bw -t rtt -o $DIR/figure6/figure6b.pdf
# PCC comparisons
python3 plot.py heatmap -i $DIR/figure6/pcc_0.1 $DIR/figure6/cubic_0.1 -x rtt -y bw -t rtt -o $DIR/figure6/figure6a_pcc.pdf
python3 plot.py heatmap -i $DIR/figure6/pcc_10 $DIR/figure6/cubic_10 -x rtt -y bw -t rtt -o $DIR/figure6/figure6b_pcc.pdf
python3 plot.py heatmap -i $DIR/figure6/pcc_0.1 $DIR/figure6/bbr_0.1 -x rtt -y bw -t rtt -o $DIR/figure6/figure6a_pcc_bbr.pdf
python3 plot.py heatmap -i $DIR/figure6/pcc_10 $DIR/figure6/bbr_10 -x rtt -y bw -t rtt -o $DIR/figure6/figure6b_pcc_bbr.pdf

python3 plot.py line -i $DIR/figure7/bbr $DIR/figure7/bbr_11_10 $DIR/figure7/bbr_3_2/ $DIR/figure7/cubic/ $DIR/figure7/reno $DIR/figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y goodput -o $DIR/figure7a.pdf

python3 plot.py line -i $DIR/figure7/bbr $DIR/figure7/bbr_11_10 $DIR/figure7/bbr_3_2/ $DIR/figure7/cubic/ $DIR/figure7/reno $DIR/figure7/pcc -n "BBR" "BBR1.1" "BBR1.5" "Cubic" "Reno" "PCC" -x loss -y retransmits -o $DIR/figure7b.pdf

python3 plot.py line -i $DIR/figure8/ --split-host -n "BBR" "Cubic" -x buffer_size -y goodput -o $DIR/figure8a.pdf --add-total --logx
python3 plot.py line -i $DIR/figure8/ --split-host -n "BBR" "Cubic" -x buffer_size -y retransmits -o $DIR/table1.pdf --logx
python3 plot.py line -i $DIR/figure8_pcc/ --split-host -n "PCC" "Cubic" -x buffer_size -y goodput -o $DIR/figure8a_pcc.pdf --add-total --logx
python3 plot.py line -i $DIR/figure8_pcc_bbr/ --split-host -n "PCC" "BBR" -x buffer_size -y goodput -o $DIR/figure8a_pcc_bbr.pdf --add-total --logx
