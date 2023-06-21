# MyNode 使用 packed_dag_block 函数

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
path = 'D:\\MyProject\\Python\\Shard\\log\\' + 'mylog - shard_dag_sync - ' + name + '.log'
file = os.open(path, os.O_CREAT)
os.close(file)
file_handler = logging.FileHandler(path)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 本地 ip
local_ip_base = '127.0.0.1'

node_num = 100
shard_num = 16
trans_num = int(80/shard_num)

num = 79

# 记录配置信息
logger.info(f'>>>>>>>>>>>>>>>>>>>>> node number : {node_num} - shard number: {shard_num} - trans number : {trans_num * shard_num} # <<<<<<<<<<<<<<<<<<<')

# 创建节点
nodes = []
for i in range(node_num):
    node = Node(local_ip_base, 30000 + i)
    nodes.append(node)

# 创建分片
shards = []
for i in range(shard_num):
    shard = Shard(i)
    shards.append(shard)

# 分片添加节点
for i, node in enumerate(nodes):
    shards[i % shard_num].add_peer(node)

# 建立同步节点
syncs = []
for i in range(shard_num):
    sync = SyncNode(i, local_ip_base, 40000 + i, shard_num)
    # 启动同步节点
    sync.start()
    syncs.append(sync)

sync_addr_list = []
for sync in syncs:
    sync_addr_list.append((sync.local_ip, sync.local_port))

for sync in syncs:
    for i, addr in enumerate(sync_addr_list):
        if i != sync.node_id:
            sync.sync_addr_list.append(addr)

# 分片添加同步地址
for i, shard in enumerate(shards):
    shard.sync_addr = sync_addr_list[i]

for shard in shards:
    # 启动分片
    shard.start()

# 监视器
monitor = Mointor(nodes)

# 分片轮次划分
partition = Partitioning(nodes, shards, monitor)

# 创建片间共识模块
config = Cross_Consensus(shards, partition)


# 创建路由节点
routers = []
for i in range(shard_num):
    router = Router(i, local_ip_base, 60000 + i, config)
    routers.append(router)

# 注册分片
for router in routers:
    for shard in shards:
        router.add_shard(shard)
    # 启动路由
    router.start()

# 启动交易
def gogo(trans_num, shard):
    for i in range(trans_num):
        shard.dag_consensus_inter()
        time.sleep(random.uniform(0.02, 0.05))

for shard in shards:
    thr = threading.Thread(target=gogo, args=(trans_num, shard))
    thr.start()


def draw(shards, interval, num_stop):
    plt.style.use('seaborn')  # 设置图表风格
    plt.figure()  # 创建图表对象
    plt.ion()  # 开启交互模式

    y1 = []
    y2 = []
    while True:
        counter = 0
        block_trans = 0
        for shard in shards:
            counter += shard.counter
            block_trans += shard.blockchain.get_trans_num()
        y1.append(counter)
        x1 = [i for i in range(1, len(y1) + 1)]

        y2.append(block_trans)
        x2 = [i for i in range(1, len(y2) + 1)]

        plt.plot(x1, y1, color='blue')  # 绘制折线图
        plt.plot(x2, y2, color='red')  # 绘制折线图

        plt.tight_layout()  # 调整子图之间的间距
        plt.draw()
        plt.pause(interval)  # 暂停interval秒
        if block_trans > num:
            break

    print(f'y1: {y1}')
    print(f'y2: {y2}')

    y1 = y1[1:]
    y2 = y2[1:]
    for i in range(len(y1) - 1, -1, -1):
        if y1[i]==y1[i-1]:
            y1 = y1[:-1]
        else:
            break
    for i in range(len(y2) - 1, -1, -1):
        if y2[i]==y2[i-1]:
            y2 = y2[:-1]
        else:
            break
    tps1 = y1[-1] / len(y1)
    tps2 = y2[-1] / len(y2)

    logger.info(f'>>>>>>>>>>>>>>>>>>>>> counter result is : {y1} <<<<<<<<<<<<<<<<<<<')
    logger.info(f'>>>>>>>>>>>>>>>>>>>>> blockchain_trans result is : {y2} <<<<<<<<<<<<<<<<<<<')

    logger.info(f'>>>>>>>>>>>>>>>>>>>>> tps1 : {tps1} <<<<<<<<<<<<<<<<<<<')
    logger.info(f'>>>>>>>>>>>>>>>>>>>>> tps2 : {tps2} <<<<<<<<<<<<<<<<<<<')

    rts = []
    cts = []
    for i, sync in enumerate(syncs):
        logger.info(
            f'>>>>>>>>>>>>>>>>>>>>> sync {i} time_consensus result is : {sync.time_consensus} <<<<<<<<<<<<<<<<<<<')
        logger.info(
            f'>>>>>>>>>>>>>>>>>>>>> sync {i} record_consensus result is : {sync.record_time} <<<<<<<<<<<<<<<<<<<')
        cts.append(sync.time_consensus)
        rts.append(sync.record_time)

    rt_mins = []
    ct_mins = []
    for rt in rts:
        rt_mins.append(min(rt))
    for ct in cts:
        ct_mins.append(min(ct))

    r_min = min(rt_mins)
    c_min = min(ct_mins)

    latency = c_min - r_min

    print(f'latency: {latency}')
    logger.info(f'>>>>>>>>>>>>>>>>>>>>> latency is : {latency} <<<<<<<<<<<<<<<<<<<')

    plt.ioff()  # 关闭交互模式
    plt.show()  # 显示最终图表


thr = threading.Thread(target=draw, args=(shards, 1, trans_num * shard_num))
thr.start()
# thr.join()

# time.sleep(40)
# counter = 0
# block_trans = 0
# consensus_block_trans = 0
# for shard in shards:
#     counter += shard.counter
#     block_trans += shard.blockchain.get_trans_num()
#
#
# print(counter)
# print(block_trans)
# print(config.get_trans_num())


