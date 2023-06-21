import numpy as np
import matplotlib.pyplot as plt

ours4 = [53.333333333333336, 16.0, 3.2, 0.6349206349206349, 0.2807017543859649]
ours8 = [0, 53.333333333333336, 12.8, 3.7209302325581395, 0.9968847352024922]
ours16 = [0, 0, 29.09090909090909, 11.228070175438596, 3.2]
ours32 = [0, 0, 0, 24.150943396226417, 24.150943396226417]
ours64 = [0, 0, 0, 0, 19.541984732824428]

values = np.array([ours4, ours8, ours16, ours32, ours64])  # 每个子数组的长度与类别数量相同
values = values.T # 行列互换

categories = ['shard 4', 'shard 8', 'shard 16', 'shard 32', 'shard 64']
group_names = ['16', '32', '64', '128', '256']


# 创建画布和坐标系
fig, ax = plt.subplots()
# 计算每个分组的中心位置
bar_width = 0.2
bar_positions = np.arange(len(group_names))

# 绘制分组条形图
for i in range(len(categories)):
    ax.bar(bar_positions + i*bar_width, values[:, i], width=bar_width, label=categories[i])

# 设置刻度标签和标题
ax.set_xticks(bar_positions + (len(categories) - 1) * bar_width / 2)
ax.set_xticklabels(group_names)
ax.set_xlabel('node  number')
ax.set_ylabel('Throughput')
ax.set_title('Throughput comparison for different nodes and shard counts')

# 添加图例
ax.legend()

# 显示图形
plt.show()