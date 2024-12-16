import matplotlib.pyplot as plt
from matplotlib import rcParams

# 配置中文字体为宋体，并设置字体大小为五号
rcParams['font.sans-serif'] = ['SimSun']  # 设置中文字体为宋体
rcParams['axes.unicode_minus'] = False  # 解决坐标轴负号显示问题
rcParams['font.size'] = 10.5  # 五号字体，对应大约 10.5 pt
# node_num = 80
x = [4, 6, 8, 10, 12, 14, 16, 18, 20]
ydag_tps = [1.6, 3.0, 5.333333333333333, 6.666666666666667, 7.2, 9.333333333333334, 16, 20.5, 29.0]
ydl_tps = [1.1428571428571428, 2.5714285714285716, 4.571428571428571, 5.0, 5.142857142857143, 7.0, 14, 17.5, 19.0]
ydag_latency = [0.030998945236206055, 0.0619354248046875, 0.17650127410888672, 0.583784818649292, 0.9322657585144043, 1.6984190940856934, 2.4357223510742188, 4.797174692153931, 6.804000377655029]
ydl_latency = [0.27924680709838867, 0.6927130222320557, 0.7586474418640137, 2.174354314804077, 4.7040252685546875, 8.022475481033325, 12.012694597244263, 16.494342803955078, 22.939006805419922]

ydag_tps60 = [4.555555555555555, 7.043478260869565, 13.333333333333334, 17.77777777777778, 22.285714285714285, 28.0]
ydl_tps60 = [2.526315789473684,  4.0, 6.153846153846154, 7.5, 10, 19.5]
ydag_latency60 = [0.07140374183654785, 0.11285781860351562, 0.27750277519226074, 0.8611736297607422, 1.41672682762146, 2.8529481887817383]
ydl_latency60 = [0.2769954204559326, 0.625550508499145, 1.5373051166534424, 2.3102965354919434, 4.284397840499878, 6.16729998588562]

ydag_tps100 = [1.6842105263157894, 3.673469387755102, 5.333333333333333, 6.4, 10.434782608695652, 18.666666666666668, 24.9]
ydl_tps100 = tps1 = [1.1764705882352942, 2.0, 2.909090909090909, 3.5294117647058822, 5.666666666666667, 9.333333333333334, 13.5]
ydag_latency100 = [0.041188716888427734, 0.11443257331848145, 0.3112828731536865, 1.0034153461456299, 1.6825463771820068, 2.2835230827331543, 4.049634218215942]
ydl_latency100 = [0.369796800613403, 0.603966021537708, 0.9489102363586426, 1.171175241470337, 4.424471139907837, 9.786924600601196, 12.860787391662598]

ydag_tps = [x * 1024 for x in ydag_tps]
ydl_tps = [x * 1024 for x in ydl_tps]
ydag_tps60 = [x * 1024 for x in ydag_tps60]
ydl_tps60 = [x * 1024 for x in ydl_tps60]
ydag_tps100 = [x * 1024 for x in ydag_tps100]
ydl_tps100 = [x * 1024 for x in ydl_tps100]

# 创建画布和坐标系
fig, ax = plt.subplots()

plt.plot(ydl_tps60, ydl_latency60, marker='o', label='DL-60', linewidth=1.5, color="#D9958F")
plt.plot(ydag_tps60, ydag_latency60, marker='^', label='ours-60', linewidth=1.5, color="#7E649E")
plt.plot(ydl_tps, ydl_latency, marker='*', label='DL-80', linewidth=1.5, color="#31859B")
plt.plot(ydag_tps, ydag_latency, marker='+', label='ours-80', linewidth=1.5, color="#7F7F7F")
plt.plot(ydl_tps100, ydl_latency100, marker='s', label='DL-100', linewidth=1.5, color="#BF9000")
plt.plot(ydag_tps100, ydag_latency100, marker='x', label='ours-100', linewidth=1.5, color="#EA700D")


# 设置横纵坐标标签
plt.xlabel('吞吐量（交易量/秒）')
plt.ylabel('交易延迟（秒）')

# 设置图例
plt.legend()
# plt.title('Latency_Comparison2')

# group_names = ['4', '8', '16', '32', '64', '128', '256']
# ax.set_xticklabels(group_names)
plt.grid()
plt.show()