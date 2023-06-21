import random
import time


# 监视节点行为，获得行为参数，用于计算信誉值
class Mointor:
    def __init__(self, nodes):
        self.nodes = nodes  # 节点列表
        self.accuracy_rates = [1 for i in range(len(self.nodes))]  # 节点历史决策正确率
        self.average_response_speeds = [0 for i in range(len(self.nodes))]  # 节点平均响应速度
        self.online_duration_ratios = [1 for i in range(len(self.nodes))]  # 节点在线时长比率
        self.op = [0 for i in range(len(self.nodes))]  # 可选参数

    # 模拟获取正确率，随机
    def get_accuracy(self):
        for i in range(len(self.nodes)):
            accuracy_increase = random.uniform(-0.2, 0.2)
            pre_accuracy = self.accuracy_rates[i]

            self.accuracy_rates[i] = self.accuracy_rates[i] + accuracy_increase  # 随机生成增量
            self.accuracy_rates[i] = max(0, min(1, self.accuracy_rates[i]))  # 确保正确率在0到1之间
            while pre_accuracy < 1.0 and self.accuracy_rates[i] >= 1.0:
                self.accuracy_rates[i] = self.accuracy_rates[i] + random.uniform(-0.2, 0.0)
            self.accuracy_rates[i] = float("{:.3f}".format(self.accuracy_rates[i]))  # 保留三位小数
        return self.accuracy_rates

    # 模拟获取平均响应速度
    def get_speed(self):
        for i in range(len(self.nodes)):
            self.average_response_speeds[i] = float("{:.5f}".format(random.uniform(0.1, 0.5)))
        for i in range(int(len(self.nodes) * 0.2)):
            self.average_response_speeds[random.randint(0, len(self.nodes)-1)] = float("{:.5f}".format(random.uniform(0.5, 1)))
        for i in range(int(len(self.nodes) * 0.1)):
            self.average_response_speeds[random.randint(0, len(self.nodes)-1)] = float("{:.5f}".format(random.uniform(1, 2)))
        for i in range(int(len(self.nodes) * 0.2)):
            self.average_response_speeds[random.randint(0, len(self.nodes)-1)] = float("{:.5f}".format(random.uniform(0.05, 0.2)))
        return self.average_response_speeds


    # 模拟获取在线时长
    def get_online(self):
        for i in range(len(self.nodes)):
            ratio_increase = random.uniform(-0.2, 0.2)
            pre_ratio = self.online_duration_ratios[i]
            self.online_duration_ratios[i] = self.online_duration_ratios[i] + ratio_increase
            self.online_duration_ratios[i] = max(0.0, min(1.0, self.online_duration_ratios[i]))  # 确保正确率在0到1之间
            while pre_ratio < 1.0 and self.online_duration_ratios[i] >= 1.0:
                self.online_duration_ratios[i] = self.online_duration_ratios[i] + random.uniform(-0.2, 0.0)
            self.online_duration_ratios[i] = float("{:.3f}".format(self.online_duration_ratios[i]))
        return self.online_duration_ratios

if __name__ == "__main__":
    m = Mointor([0 for i in range(16)])
    for i in range(10):
        # m.get_accuracy()
        m.get_speed()
        # m.get_online()

        # print(f'accuracy_rates: {m.accuracy_rates}')
        print(f'average_response_speeds: {m.average_response_speeds}')
        # print(f'online_duration_ratios: {m.online_duration_ratios}')
        print()
        time.sleep(2)
