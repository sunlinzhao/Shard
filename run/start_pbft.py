import time
import threading
import logging
import matplotlib.pyplot as plt

# 本地导入
from role.MyNode import *
from layer.Shard import *
from role.Router import *
from layer.Gather import *
from utils.Draw import draw
from utils.Shard_Partition import Partitioning
from utils.Monitor import Mointor
from role.SyncNode import SyncNode

'''日志的配置信息只设置一次即可，当然如果项目大，有不同的需求，可以写在配置文件里'''
# 创建日志对象
logger = logging.getLogger()
# 设置日志等级
logger.setLevel(logging.INFO)
# 配置日志格式
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
ansi_formatter = logging.Formatter('\033[32m%(asctime)s %(levelname)s %(message)s\033[0m')
# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setFormatter(ansi_formatter)
logger.addHandler(console_handler)
# 文件输出
name = str(int(time.time()))
path = 'D:\\MyProject\\Python\\Shard\\log\\' + 'mylog - pbft - ' + name + '.log'
file = os.open(path, os.O_CREAT)
os.close(file)
file_handler = logging.FileHandler(path)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 本地 ip
local_ip_base = '127.0.0.1'

node_num = 64
trans_num = 10

# 记录配置信息
logger.info(f'>>>>>>>>>>>>>>>>>>>>> node number : {node_num} - trans number : {trans_num} # <<<<<<<<<<<<<<<<<<<')

# 创建节点
nodes = []
for i in range(node_num):
    node = Node(local_ip_base, 50000 + i)
    nodes.append(node)

# 建立分片
shard = Shard(0)

# 添加节点
for node in nodes:
    shard.add_peer(node)

 # 启动分片
shard.start()

# 启动交易
def gogo(trans_num, shard):
    for i in range(trans_num):
        shard.consensus_intra()
        time.sleep(random.uniform(0.02, 0.05))

thr1 = threading.Thread(target=gogo, args=(trans_num, shard))
thr1.start()
# thr1.join()

def draw(shard, interval, num_stop):
    plt.style.use('seaborn')  # 设置图表风格
    plt.figure()  # 创建图表对象
    plt.ion()  # 开启交互模式

    y1 = []
    y2 = []
    while True:
        y1.append(shard.counter)
        x1 = [i for i in range(1, len(y1) + 1)]

        y2.append(shard.blockchain.get_trans_num())
        x2 = [i for i in range(1, len(y2) + 1)]

        plt.plot(x1, y1, color='blue')  # 绘制折线图
        plt.plot(x2, y2, color='red')  # 绘制折线图

        plt.tight_layout()  # 调整子图之间的间距
        plt.draw()
        plt.pause(interval)  # 暂停interval秒
        if shard.blockchain.get_trans_num() == num_stop:
            break

    print(f'y1: {y1}')
    print(f'y2: {y2}')
    logger.info(f'>>>>>>>>>>>>>>>>>>>>> time_pbft result is : {shard.time_pbft} <<<<<<<<<<<<<<<<<<<')
    plt.ioff()  # 关闭交互模式
    plt.show()  # 显示最终图表


thr2 = threading.Thread(target=draw, args=(shard, 1, trans_num))
thr2.start()
thr2.join()


# time.sleep(5)
# print(shard.counter)
# print(shard.blockchain.get_trans_num())
# print(len(shard.trans_pool))

# 记录结果信息
logger.info(f'>>>>>>>>>>>>>>>>>>>>> counter result is : {shard.counter} <<<<<<<<<<<<<<<<<<<')
logger.info(f'>>>>>>>>>>>>>>>>>>>>> blockchain_trans result is : {shard.blockchain.get_trans_num()} <<<<<<<<<<<<<<<<<<<')



