import matplotlib.pyplot as plt

X1 = [4, 8, 16, 32, 64, 128, 256]
pbft_tps = [10, 9.23076923076923, 3.870967741935484, 0.8888888888888888, 0.16, 0.081799591002045, 0.02466091245376079]

X2 = [16, 32, 64, 128, 256]
shard4_two_stage_tps = [40, 13.333333333333334, 3.902439024390244, 0.8695652173913043, 0.24096385542168675]
ours4 = [53.333333333333336, 16.0, 3.2, 0.6349206349206349, 0.2807017543859649]

X3 = [32, 64, 128, 256]
shard8_two_stage_tps = [64.0, 15.238095238095237, 1.7204301075268817, 1.0596026490066226]
ours8 = [53.333333333333336, 12.8, 3.7209302325581395, 0.9968847352024922]

X4 = [64, 128, 256]
shard16_two_stage_tps = [33.68421052631579, 7.032967032967033, 2.633744855967078]
ours16 = [29.09090909090909, 11.228070175438596, 3.2]

X5 = [128, 256]
shard32_two_stage_tps = [38.78787878787879, 7.57396449704142]
ours32 = [24.150943396226417, 24.150943396226417]

X5 = [256]
shard64_two_stage_tps = [24.854368932038835]
ours64 = [19.541984732824428]


# for i in range(len(X2)):
#     shard4_two_stage_tps[i] = shard4_two_stage_tps[i] / pbft_tps[i + 2]
#     ours4[i] = ours4[i] / pbft_tps[i + 2]


# 创建画布和坐标系
fig, ax = plt.subplots()

plt.plot(X2, shard4_two_stage_tps, color=(114/256, 170/256, 207/256), marker='o', label='DL')  # 设置点样式为圆形，添加标签
plt.plot(X2, ours4, color=(236/256, 93/256, 59/256), marker='^', label='ours')  # 设置点样式为圆形，添加标签
plt.plot(X1, pbft_tps, color=(253/256, 185/256, 107/256), marker='+', label='pbft')  # 设置点样式为圆形，添加标签

# 设置横纵坐标标签
plt.xlabel('node_num')
plt.ylabel('Tps')

# 设置图例
plt.legend()

# 设置自定义刻度
plt.xticks(X1)  # 设置横坐标刻度为自定义的值

# group_names = ['4', '8', '16', '32', '64', '128', '256']
# ax.set_xticklabels(group_names)
plt.show()