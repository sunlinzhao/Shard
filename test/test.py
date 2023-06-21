# from test.Node import *
#
# # 创建节点
# node1 = BlockchainNode(node_id=1, ip='127.0.0.1', port=5000, shard_id=1)
# node2 = BlockchainNode(node_id=2, ip='127.0.0.1', port=5001, shard_id=1)
# node3 = BlockchainNode(node_id=3, ip='127.0.0.1', port=5002, shard_id=2)
#
# # 设置节点之间的对等关系
# node1.add_peer(node2)
# node1.add_peer(node3)
# node2.add_peer(node1)
# node2.add_peer(node3)
# node3.add_peer(node1)
# node3.add_peer(node2)
#
# # 启动节点
# node1.start()
# node2.start()
# node3.start()
#
# node2.start_pbft_consensus()

from role.SyncNode import SyncNode
from utils.MyUtils import generate_random_id

import random
import threading


import numpy as np
import matplotlib.pyplot as plt

def custom_function(x):
    return 1 / (1 + np.exp(-10*x))

x = np.linspace(-1, 1, 100)
y = custom_function(x)

plt.plot(x, y)
plt.show()

print(y)






# if __name__ == '__main__':
    # # 本地 ip
    # local_ip_base = '127.0.0.1'
    #
    # # 建立同步节点
    # sync1 = SyncNode(0, local_ip_base, 40000)
    # sync2 = SyncNode(1, local_ip_base, 40001)
    # sync3 = SyncNode(2, local_ip_base, 40002)
    # sync4 = SyncNode(3, local_ip_base, 40003)
    #
    # # 启动同步节点
    # sync1.start()
    # sync2.start()
    # sync3.start()
    # sync4.start()
    #
    # sync_list = [sync1, sync2, sync3, sync4]
    # sync_addr_list = []
    # for sync in sync_list:
    #     sync_addr_list.append((sync.local_ip, sync.local_port))
    #
    # for sync in sync_list:
    #     for i, addr in enumerate(sync_addr_list):
    #         if i != sync.node_id:
    #             sync.sync_addr_list.append(addr)





