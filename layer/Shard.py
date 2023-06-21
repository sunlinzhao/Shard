import random
import logging
import threading
import time

# 本地导入
from layer.Blockchain import *
from utils.MyUtils import calculate_tolerance, generate_random_id

# 创建日志对象
logger = logging.getLogger()

# 模拟分片
class Shard:
    def __init__(self, shard_id):
        self.shard_id = shard_id

        self.sync_addr = None

        self.peers = []
        self.blockchain = BlockChain(self.shard_id)
        self.block = Block()
        # 路由地址
        self.router_addrs = []
        # 交易池
        self.trans_pool = []
        # self.Tx_Pool = []
        # 跨分片共识辅助数组
        self.cross_ids = []
        # 交易计数
        self.counter = 0

        self.wait_confirmation = []  # 等待状态查询结果的队列
        self.wait_reference = []  # 等待引用的区块 (由于模拟，所以只存储 ID)
        # 为了防止数据冲突，设置锁
        self.lock_wait_confirmation = threading.RLock()
        self.lock = threading.RLock()
        self.lock_trans = threading.RLock()
        self.lock_wait_reference = threading.RLock()

        # 记录共识时间
        self.time_consensus = []

        self.time_pbft = []

    # 启动分片
    def start(self):
        logger.info(f'| Shard [{self.shard_id}] started !')
        # 启动节点
        for peer in self.peers:
            peer.start()

    # 获得分片节点数量
    def get_num(self):
        return len(self.peers)
    # 分片添加节点
    def add_peer(self, peer):
        # 分配节点ID 和 分片标识ID
        peer.shard_id = self.shard_id
        peer.node_id = len(self.peers)
        peer.shard = self       # 将分片对象本身传递给各个节点
        peer.history_partition.append(self.shard_id)    # 记录历史分片
        # 建立分片内节点间的 对等连接
        for node in self.peers:
            peer.peers.append(node)
            node.peers.append(peer)
        # 加入分片
        self.peers.append(peer)

    def find_cross_id(self, cross_id):
        index = 0
        for temp in self.cross_ids:
            if temp[0] == cross_id:
                return index
            index += 1
        return None

    def find_trans_pool(self, number):
        index = 0
        for temp in self.trans_pool:
            if number == temp[0]:
                return index
            index += 1
        return None
    def find_wait_confirmation(self, signal):
        index = 0
        for item in self.wait_confirmation:
            if signal == item[0]:
                return index
            index += 1
        return None

    # 添加交易
    def add_trans(self, trans, node_id):
        number = trans['number']
        index = self.find_trans_pool(number)
        if index == None:
            temp = [number, trans, set(), False]
            temp[2].add(node_id)
            with self.lock_trans:
                self.trans_pool.append(temp)
        else:
            with self.lock_trans:
                self.trans_pool[index][2].add(node_id)
            if len(list(self.trans_pool[index][2])) >= calculate_tolerance(len(self.peers)) + 1: # f + 1 就够确认
                if self.trans_pool[index][3] == False:
                    self.trans_pool[index][3] = True
                    # 添加片内共识结果
                    with self.lock_trans:
                        self.block.add_trans(self.trans_pool[index][1])
                        self.counter += 1
                        self.time_pbft.append(time.time())
                    # 发给同步节点记录
                    trans['tag'] = 'Record'
                    peer = random.choice(self.peers)
                    leader = peer.find_leader() # 寻找主节点
                    if leader != None:
                        leader.pool.submit(leader.send_msg, trans, self.sync_addr)

    # 分片内共识
    def consensus_intra(self):
        # 随机发起片内共识，交给 Leader 主导
        # 分片内任意节点发起一次交易，就是一次共识
        while True:
            peer = random.choice(self.peers)
            peer_to = random.choice(self.peers)
            if peer != peer_to:
                data = {'tag': 'INTRA',
                        'round': peer.round,
                        'shard_id': self.shard_id,
                        'node_id': peer.node_id,
                        'addr': (peer.local_ip, peer.local_port),
                        'ID': peer.ID
                        }
                peer.send_msg(data, (peer_to.local_ip, peer_to.local_port))
                break

    def consensus_inter_non_sync(self):
        # 随机发起片内共识，交给 Leader 主导
        # 分片内任意节点发起一次交易，就是一次共识
        while True:
            peer = random.choice(self.peers)
            peer_to = random.choice(self.peers)
            if peer != peer_to:
                data = {'tag': 'INTER_ready',
                        'round': peer.round,
                        'shard_id': self.shard_id,
                        'node_id': peer.node_id,
                        'addr': (peer.local_ip, peer.local_port),
                        'ID': peer.ID
                        }
                peer.send_msg(data, (peer_to.local_ip, peer_to.local_port))
                break
    # 分片间的共识
    def consensus_inter(self):
        # 分片间的共识，由分片内主节点发起，将打包好的区块转发给路由节点，路由节点转发给其他分片进行验证投票，通过后进入全局状态
        # 随机发起片间共识，向同步节点查询状态
        # 分片任意节点发起一次交易，就是一次共识
        peer = random.choice(self.peers)
        signal = generate_random_id()
        data = {'tag': 'Query',
                'round': peer.round,
                'content': '',
                'signal': signal,
                'addr': (peer.local_ip, peer.local_port)
                }
        msg = {'tag': 'INTER_ready',
                'round': peer.round,
                'shard_id': self.shard_id,
                'node_id': peer.node_id,
                'addr': (peer.local_ip, peer.local_port),
                'ID': peer.ID
                }
        with self.lock_wait_confirmation:
            self.wait_confirmation.append([signal, msg, False])
        peer.pool.submit(peer.send_msg, data, self.sync_addr)

    def dag_consensus_inter(self):
        # 分片间的共识，由分片内主节点发起，将打包好的区块转发给路由节点，路由节点转发给其他分片进行验证投票，通过后进入全局状态
        # 随机发起片间共识，向同步节点查询状态
        # 分片任意节点发起一次交易，就是一次共识
        peer = random.choice(self.peers)
        signal = generate_random_id()
        data = {'tag': 'DAG_Query',
                'round': peer.round,
                'content': '',
                'signal': signal,
                'addr': (peer.local_ip, peer.local_port)
                }
        msg = {'tag': 'INTER_ready',
                'round': peer.round,
                'shard_id': self.shard_id,
                'node_id': peer.node_id,
                'addr': (peer.local_ip, peer.local_port),
                'ID': peer.ID
                }
        with self.lock_wait_confirmation:
            self.wait_confirmation.append([signal, msg, False])
        peer.pool.submit(peer.send_msg, data, self.sync_addr)




    # def find_Tx_Pool(self, cross_id):
    #     index = 0
    #     for temp in self.Tx_Pool:
    #         if cross_id == temp[0]:
    #             return index
    #         index += 1
    #     return None
    #
    #     # 获取当前分片内未完成交易
    #     def get_False_trans(self):
    #         false_trans = [trans for trans in self.trans_pool if trans[3] == False]
    #         index = [index for index, trans in enumerate(self.trans_pool) if trans[3] == False]
    #         with self.lock:
    #             for ind in index:
    #                 self.trans_pool[ind][3] = True
    #         return false_trans
    #
    #     # 获取当前分片未完全提交区块
    #     def get_False_Tx(self):
    #         false_Tx = [Tx for Tx in self.Tx_Pool if Tx[2] == False]
    #         index = [index for index, Tx in enumerate(self.Tx_Pool) if Tx[2] == False]
    #         with self.lock:
    #             for ind in index:
    #                 self.Tx_Pool[ind][2] = True
    #         return false_Tx
    #
    #     # 新一轮划分，处理未完成交易
    #     def process_false(self):
    #         false_trans = self.get_False_trans()
    #         for temp in false_trans:
    #             trans = temp[1]
    #             while True:
    #                 peer = random.choice(self.peers)
    #                 peer_to = random.choice(self.peers)
    #                 if peer != peer_to:
    #                     new_trans_data = {'tag': trans['msg']['tag'],
    #                                       'round': peer.round,
    #                                       'shard_id': peer.shard_id,
    #                                       'node_id': peer.node_id,
    #                                       'addr': (peer.local_ip, peer.local_port),
    #                                       'ID': peer.ID
    #                                       }
    #                     peer.send_msg(new_trans_data, (peer_to.local_ip, peer_to.local_port))
    #                     break
    #         false_Tx = self.get_False_Tx()
    #         for temp in false_Tx:
    #             Tx = temp[1]
    #             peer = random.choice(self.peers)
    #             new_Tx_data = {'tag': Tx['tag'],
    #                            'round': peer.round,
    #                            'shard_id': peer.shard_id,
    #                            'node_id': peer.node_id,
    #                            'block_id': Tx['block_id'],
    #                            'data': Tx['data']}
    #             router = random.choice(self.router_addrs)
    #             peer.send_msg(new_Tx_data, router)
    #
    #             cross_id = [new_Tx_data['round'], new_Tx_data['shard_id'], new_Tx_data['node_id'],
    #                         new_Tx_data['block_id']]
    #             index = self.find_Tx_Pool(cross_id)
    #             with self.lock:
    #                 if index == None:
    #                     self.Tx_Pool.append([cross_id, new_Tx_data, False])
    #                 else:
    #                     self.Tx_Pool[index] = [cross_id, new_Tx_data, False]


if __name__ == '__main__':
    s = Shard(0)
    s.process_false()