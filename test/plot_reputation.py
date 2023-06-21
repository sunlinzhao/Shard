import math

import matplotlib.pyplot as plt
import numpy as np

step = 0.1
values1 = [round(x, 2) for x in np.arange(1, 0 - step, -step)]
values2 = [round(x, 2) for x in np.arange(1, 0 - step, -step)]
values3 = [round(x, 2) for x in np.arange(1, 0 - step, -step)]


print(values1)
values4 = [round(x, 2) for x in np.arange(0, 1 + step, step)]
values5 = [round(x, 2) for x in np.arange(0, 1 + step, step)]
values6 = [round(x, 2) for x in np.arange(0, 1 + step, step)]
print(values4)
record = [None, None]
repus1 = []
for i in range(len(values1)):
    av = 0.6 * values1[i] + 0.2 * values2[i] + 0.2 * values3[i]
    if None in record:
        penalty = 0
    else:
        calculation = lambda x: x**3
        penalty = calculation(record[1] - record[0])
    repu = (2*av / (av + math.exp(-10*penalty)))**3

    repus1.append(repu)
    record[0] = record[1]
    record[1] = repu
# -ln ( (1 / x) - 1)
print(repus1)

record = [None, None]
repus2 = []
for i in range(len(values4)):
    av = 0.6 * values4[i] + 0.2 * values5[i] + 0.2 * values6[i]
    if None in record:
        penalty = 0
    else:
        calculation = lambda x:  x**3
        penalty = calculation(record[1] - record[0])
    repu = (2*av / (av + math.exp(-10*penalty)))**3
    repus2.append(repu)
    record[0] = record[1]
    record[1] = repu

print(repus2)

step2 = 0.15
values7 = [round(x, 2) for x in np.arange(1, 0 - step2, -step2)]
values8 = [round(x, 2) for x in np.arange(1, 0 - step2, -step2)]
values9 = [round(x, 2) for x in np.arange(1, 0 - step2, -step2)]

values10 = [round(x, 2) for x in np.arange(0, 1 + step2, step2)]
values11 = [round(x, 2) for x in np.arange(0, 1 + step2, step2)]
values12 = [round(x, 2) for x in np.arange(0, 1 + step2, step2)]

record = [None, None]
repus3 = []
for i in range(len(values7)):
    av = 0.6 * values7[i] + 0.2 * values8[i] + 0.2 * values9[i]
    if None in record:
        penalty = 0
    else:
        calculation = lambda x: x**3
        penalty = calculation(record[1] - record[0])
    repu = (2*av / (av + math.exp(-10*penalty)))**3

    repus3.append(repu)
    record[0] = record[1]
    record[1] = repu
print(repus3)

record = [None, None]
repus4 = []
for i in range(len(values10)):
    av = 0.6 * values10[i] + 0.2 * values11[i] + 0.2 * values12[i]
    if None in record:
        penalty = 0
    else:
        calculation = lambda x: x**3
        penalty = calculation(record[1] - record[0])
    repu = (2*av / (av + math.exp(-10*penalty)))**3

    repus4.append(repu)
    record[0] = record[1]
    record[1] = repu
print(repus4)

step2 = 0.2
values13 = [round(x, 2) for x in np.arange(1, 0 - step2, -step2)]
values14 = [round(x, 2) for x in np.arange(1, 0 - step2, -step2)]
values15 = [round(x, 2) for x in np.arange(1, 0 - step2, -step2)]

values16 = [round(x, 2) for x in np.arange(0, 1 + step2, step2)]
values17 = [round(x, 2) for x in np.arange(0, 1 + step2, step2)]
values18 = [round(x, 2) for x in np.arange(0, 1 + step2, step2)]

record = [None, None]
repus5 = []
for i in range(len(values13)):
    av = 0.6 * values13[i] + 0.2 * values14[i] + 0.2 * values15[i]
    if None in record:
        penalty = 0
    else:
        calculation = lambda x: x**3
        penalty = calculation(record[1] - record[0])
    repu = (2*av / (av + math.exp(-10*penalty)))**3

    repus5.append(repu)
    record[0] = record[1]
    record[1] = repu
print(repus5)

record = [None, None]
repus6 = []
for i in range(len(values16)):
    av = 0.6 * values16[i] + 0.2 * values17[i] + 0.2 * values18[i]
    if None in record:
        penalty = 0
    else:
        calculation = lambda x: x**3
        penalty = calculation(record[1] - record[0])
    repu = (2*av / (av + math.exp(-10*penalty)))**3

    repus6.append(repu)
    record[0] = record[1]
    record[1] = repu
print(repus6)


# 创建画布和坐标系
fig, ax = plt.subplots()
values1 =  [-x for x in values1]
values7 = [-x for x in values7]
plt.plot([i for i in range(len(repus1))], repus1, marker='*', label='Byzantine1', linewidth=1)
plt.plot([i for i in range(len(repus3))], repus3, marker='+', label='Byzantine2', linewidth=1)
plt.plot([i for i in range(len(repus5))], repus5, marker='.', label='Byzantine3', linewidth=1)

# plt.title("The Variation of Byzantine Node Reputation Values")


# plt.grid()

# 设置横纵坐标标签
plt.xlabel('Round')
plt.ylabel('Reputation Values')

# # 反转横坐标刻度
# plt.gca().invert_xaxis()


# 设置图例
plt.legend()
plt.show()


# 创建画布和坐标系
fig, ax = plt.subplots()


plt.plot([i for i in range(len(repus2))], repus2, marker='.', label='Honest1', linewidth=1)
plt.plot([i for i in range(len(repus4))], repus4, marker='^', label='Honest2', linewidth=1)
plt.plot([i for i in range(len(repus6))], repus6, marker='.', label='Honest3', linewidth=1)
# plt.title("The Variation of Honest Node Reputation Values")

# 设置横纵坐标标签
plt.xlabel('Round')
plt.ylabel('Reputation Values')

plt.legend()
plt.show()