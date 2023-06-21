import matplotlib.pyplot as plt
import threading

# 动态绘图
class draw(threading.Thread):
    def __init__(self, config, shards):
        threading.Thread.__init__(self)
        self.config  = config
        self.shards = shards

    def run(self):
        plt.style.use('seaborn')  # 设置图表风格
        plt.figure()  # 创建图表对象
        plt.ion()  # 开启交互模式

        y1 = []
        y2 = []
        while True:
            y1.append(self.config.get_trans_num())
            x1 = [i for i in range(1,len(y1)+1)]

            num = 0
            for shard in self.shards:
                num += shard.counter
            y2.append(num)
            x2 = [i for i in range(1,len(y2)+1)]

            plt.plot(x1, y1, color='blue')  # 绘制折线图
            plt.plot(x2, y2, color='red')  # 绘制折线图

            plt.tight_layout()  # 调整子图之间的间距
            plt.draw()
            plt.pause(1)  # 暂停1秒

        plt.ioff()  # 关闭交互模式
        plt.show()  # 显示最终图表

if __name__ == '__main__':
    pass