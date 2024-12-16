import matplotlib.pyplot as plt
from matplotlib import rcParams

# 配置中文字体为宋体，并设置字体大小为五号
rcParams['font.sans-serif'] = ['SimSun']  # 设置中文字体为宋体
rcParams['axes.unicode_minus'] = False  # 解决坐标轴负号显示问题
rcParams['font.size'] = 10.5  # 五号字体，对应大约 10.5 pt
# shard_num = 8
x1 = [40, 60, 80, 100, 120, 140, 160]
ydl1 = [20.0, 11.428571428571429, 9.714285714285714, 4.625, 2.75, 1.5277777777777777, 1.5]
ydag1 = [32.888888888888886, 14.8, 8.727272727272727, 6.333333333333333, 3.3125, 3.1604938271604937, 2.5943396226415096]

# shard_num = 12
x2 = [60, 80, 100, 120, 140, 160]
ydl2 = [7.333333333333333, 5.142857142857143, 4.0, 3.6, 1.8, 1.2857142857142858]
ydag2 = [27.272727272727273, 14.285714285714286, 7.911764705882353, 6.285714285714286, 5.866666666666666, 4.587301587301587]

# shard_num = 16
x3 = [80, 100, 120, 140, 160]

ydl3 = [8.0, 4.571428571428571, 2.1333333333333333, 1.1851851851851851, 1.0666666666666667]
ydag3 = [26.181818181818183, 15.157894736842104, 11.076923076923077, 7.166666666666667, 5.9772727272727275]

ydl1 = [x * 1024 for x in ydl1]
ydl2 = [x * 1024 for x in ydl2]
ydl3 = [x * 1024 for x in ydl3]
ydag1 = [x * 1024 for x in ydag1]
ydag2 = [x * 1024 for x in ydag2]
ydag3 = [x * 1024 for x in ydag3]

# 创建画布和坐标系
fig, ax = plt.subplots()

plt.plot(x1, ydl1,marker='o', label='DL-8', linewidth=1.5, color="#D9958F")
plt.plot(x1, ydag1, marker='^', label='ours-8', linewidth=1.5, color="#7E649E")
plt.plot(x2, ydl2, marker='*', label='DL-12', linewidth=1.5, color="#31859B")
plt.plot(x2, ydag2, marker='+', label='ours-12', linewidth=1.5, color="#7F7F7F")
plt.plot(x3, ydl3, marker='s', label='DL-16', linewidth=1.5, color="#BF9000")
plt.plot(x3, ydag3, marker='x', label='ours-16', linewidth=1.5, color="#EA700D")

# 设置横纵坐标标签
plt.xlabel('节点数量（个）')
plt.ylabel('吞吐量（交易量/秒）')

# plt.title('Throughput Comparison')

# 设置图例
plt.legend()
plt.grid()

# 设置自定义刻度
plt.show()