from role.MyNode import *
from layer.Shard import *
from role.Router import *
from layer.Gather import *
from utils.Draw import draw
from utils.Shard_Partition import Partitioning
from utils.Monitor import Mointor
from role.SyncNode import SyncNode

import time
import threading
import logging

if __name__ == '__main__':
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
    path = 'log\\' + 'mylog - INFO - ' + name + '.log'
    file = os.open(path, os.O_CREAT)
    os.close(file)
    file_handler = logging.FileHandler(path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


    # 本地 ip
    local_ip_base = '127.0.0.1'


    # 建立节点
    node1 = Node(local_ip_base, 50000)
    node2 = Node(local_ip_base, 50001)
    node3 = Node(local_ip_base, 50002)
    node4 = Node(local_ip_base, 50003)

    node5 = Node(local_ip_base, 50004)
    node6 = Node(local_ip_base, 50005)
    node7 = Node(local_ip_base, 50006)
    node8 = Node(local_ip_base, 50007)

    node9 = Node(local_ip_base, 50008)
    node10 = Node(local_ip_base, 50009)
    node11 = Node(local_ip_base, 50010)
    node12 = Node(local_ip_base, 50011)

    node13 = Node(local_ip_base, 50012)
    node14 = Node(local_ip_base, 50013)
    node15 = Node(local_ip_base, 50014)
    node16 = Node(local_ip_base, 50015)


    # 建立分片
    shard1 = Shard(0)
    shard1.add_peer(node1)
    shard1.add_peer(node2)
    shard1.add_peer(node3)
    shard1.add_peer(node4)

    shard2 = Shard(1)
    shard2.add_peer(node5)
    shard2.add_peer(node6)
    shard2.add_peer(node7)
    shard2.add_peer(node8)

    shard3 = Shard(2)
    shard3.add_peer(node9)
    shard3.add_peer(node10)
    shard3.add_peer(node11)
    shard3.add_peer(node12)

    shard4 = Shard(3)
    shard4.add_peer(node13)
    shard4.add_peer(node14)
    shard4.add_peer(node15)
    shard4.add_peer(node16)


    # 创建轮次划分
    nodes = [node1, node2, node3, node4, node5, node6, node7, node8, node9, node10, node11, node12, node13, node14, node15, node16]
    shards = [shard1, shard2, shard3, shard4]

    # 建立同步节点
    sync1 = SyncNode(0, local_ip_base, 40000, len(shards))
    sync2 = SyncNode(1, local_ip_base, 40001, len(shards))
    sync3 = SyncNode(2, local_ip_base, 40002, len(shards))
    sync4 = SyncNode(3, local_ip_base, 40003, len(shards))

    # 启动同步节点
    sync1.start()
    sync2.start()
    sync3.start()
    sync4.start()

    sync_list = [sync1, sync2, sync3, sync4]
    sync_addr_list = []
    for sync in sync_list:
        sync_addr_list.append((sync.local_ip, sync.local_port))

    for sync in sync_list:
        for i, addr in enumerate(sync_addr_list):
            if i != sync.node_id:
                sync.sync_addr_list.append(addr)

    # 添加同步地址
    shard1.sync_addr = sync_addr_list[0]
    shard2.sync_addr = sync_addr_list[1]
    shard3.sync_addr = sync_addr_list[2]
    shard4.sync_addr = sync_addr_list[3]

    # 启动分片
    shard1.start()
    shard2.start()
    shard3.start()
    shard4.start()

    # 监视器
    monitor = Mointor(nodes)
    # 分片轮次划分
    partition = Partitioning(nodes, shards, monitor)

    # 创建片间共识模块
    config = Cross_Consensus(shards, partition)


    # 创建 Router
    router1 = Router(0, local_ip_base, 50016, config)
    router2 = Router(1, local_ip_base, 50017, config)
    router3 = Router(2, local_ip_base, 50018, config)
    router4 = Router(3, local_ip_base, 50019, config)

    # 启动 Router
    router1.start()
    router2.start()
    router3.start()
    router4.start()

    router_list = [router1, router2, router3, router4]

    # 注册分片
    for router in router_list:
        router.add_shard(shard1)
        router.add_shard(shard2)
        router.add_shard(shard3)
        router.add_shard(shard4)

    # for i in range(50):
    #     shard1.consensus_inter()
    #     time.sleep(random.uniform(0.01, 0.05))

    draw = draw(config, [shard1,shard2,shard3,shard4])
    draw.start()

    # 发起共识
    config.start_go()

    # 发起共识
    # thr1 = threading.Thread(target=gogo, args=(shard1, ))
    # thr2 = threading.Thread(target=gogo, args=(shard2, ))
    # thr3 = threading.Thread(target=gogo, args=(shard3, ))
    # thr4 = threading.Thread(target=gogo, args=(shard4, ))
    #
    # thr1.start()
    # thr2.start()
    # thr3.start()
    # thr4.start()
    #
    # thr1.join()
    # thr2.join()
    # thr3.join()
    # thr4.join()


    time.sleep(30)

    # 打印区块链
    shard1.blockchain.print_chain()
    shard2.blockchain.print_chain()
    shard3.blockchain.print_chain()
    shard4.blockchain.print_chain()


    time.sleep(10)
    config.print_info()

    print(shard1.blockchain.get_trans_num() + shard2.blockchain.get_trans_num() + shard3.blockchain.get_trans_num() + shard4.blockchain.get_trans_num() +
          shard1.block.get_len() + shard2.block.get_len() + shard3.block.get_len() + shard4.block.get_len())
    time.sleep(5)
    print(config.get_trans_num())

