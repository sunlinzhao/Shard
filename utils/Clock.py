import time
import threading
import logging

from utils.MyUtils import generate_random_id
from layer.Blockchain import Block

# 逻辑定时器，定时打包交易
class LogicalClock:
    def __init__(self, interval, func, args):
        self.time = 0
        self.timer = None
        self.interval = interval # 操作执行的时间间隔
        self.func = func
        self.args = args

    def tick(self):
        # 每次递增时钟后，检查是否需要执行操作
        if self.time % self.interval == 0:
            self.do_operation()

        self.time += 1
        # print("当前时间:", self.time)

        # 继续下一次时钟递增
        self.timer = threading.Timer(1, self.tick)
        self.timer.start()

    def start(self):
        # 启动逻辑时钟
        self.timer = threading.Timer(1, self.tick)
        self.timer.start()

    def stop(self):
        # 停止逻辑时钟
        if self.timer:
            self.timer.cancel()

    def do_operation(self):
        self.func()

if __name__ == '__main__':
    # 创建逻辑时钟对象
    clock = LogicalClock()

    # 启动逻辑时钟
    clock.start()

    # 模拟时间的流逝
    # time.sleep(20)

    # 停止逻辑时钟
    # clock.stop()
