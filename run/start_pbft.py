import time
import threading
import logging
import os
import random
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

# 设置日志
def setup_logger():
    logger = logging.getLogger()
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
    log_dir = r'D:\MyProject\Python\Shard_my\log'
    os.makedirs(log_dir, exist_ok=True)  # 确保日志文件夹存在
    log_path = os.path.join(log_dir, f'mylog - pbft - {name}.log')
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger()

# 配置本地信息
local_ip_base = '127.0.0.1'
node_num = 64
trans_num = 10

# 记录配置信息
logger.info(f'>>>>>>>>>>>>>>>>>>>>> node number : {node_num} - trans number : {trans_num} # <<<<<<<<<<<<<<<<<<<')

# 创建节点
nodes = [Node(local_ip_base, 3000 + i) for i in range(node_num)]

# 创建分片并添加节点
shard = Shard(0)
for node in nodes:
    shard.add_peer(node)

# 启动分片
shard.start()

# 启动交易线程
def gogo(trans_num, shard):
    for _ in range(trans_num):
        shard.consensus_intra()
        time.sleep(random.uniform(0.2, 0.5))

thr1 = threading.Thread(target=gogo, args=(trans_num, shard))
thr1.start()

# 更新图表数据的线程
def update_graph_data(shard, interval, num_stop, y1, y2):
    while shard.blockchain.get_trans_num() < num_stop:
        y1.append(shard.counter)
        y2.append(shard.blockchain.get_trans_num())
        time.sleep(interval)

# 绘图函数
def draw_graph(y1, y2):
    plt.style.use('seaborn')  # 设置图表风格
    plt.figure()  # 创建图表对象
    plt.ion()  # 开启交互模式

    x1 = [i for i in range(1, len(y1) + 1)]
    x2 = [i for i in range(1, len(y2) + 1)]

    plt.plot(x1, y1, color='blue', label='Shard Counter')
    plt.plot(x2, y2, color='red', label='Transaction Count')

    plt.tight_layout()  # 调整子图之间的间距
    plt.legend()
    plt.draw()

    # 记录结果信息
    logger.info(f'>>>>>>>>>>>>>>>>>>>>> time_pbft result is : {shard.time_pbft} <<<<<<<<<<<<<<<<<<<')
    logger.info(f'>>>>>>>>>>>>>>>>>>>>> counter result is : {shard.counter} <<<<<<<<<<<<<<<<<<<')
    logger.info(f'>>>>>>>>>>>>>>>>>>>>> blockchain_trans result is : {shard.blockchain.get_trans_num()} <<<<<<<<<<<<<<<<<<<')

    plt.ioff()  # 关闭交互模式
    plt.show()  # 显示最终图表

# 数据收集线程
y1, y2 = [], []
thr2 = threading.Thread(target=update_graph_data, args=(shard, 1, trans_num, y1, y2))
thr2.start()

# 主线程负责绘图
thr2.join()  # 等待数据收集线程结束
draw_graph(y1, y2)

# 结束后清理资源
thr1.join()
