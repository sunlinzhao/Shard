import queue
import msgpack
import hashlib
import logging
import threading
import random
import time

from utils.MyUtils import calculate_tolerance
from concurrent.futures import ThreadPoolExecutor


logger = logging.getLogger()
# 分片间的共识结果收集确认
class Cross_Consensus:
    def __init__(self, shards, partition):
        self.chain = queue.Queue()
        self.gather = []
        self.lock_gether = threading.RLock()
        self.lock = threading.RLock()
        # 划分轮次
        self.shards = shards
        self.partition = partition
        self.trans_interval = 1200  # 全局每产生 3200 个交易划分一个轮次
        self.flag = None

        # 记录区块公式时间
        self.time_consensus = []

        self.pool = ThreadPoolExecutor(100)

    # 判断并划分轮次
    def run_partition(self):
        if self.get_trans_num() % self.trans_interval == 0 and self.get_len() > 0:
            hash_value = list(self.chain.queue)[-1]['hash_value']
            if self.flag != hash_value:
                self.flag = hash_value
                # 划分轮次
                self.partition.shard_partitioning()
                # 新一轮次交易启动
                self.start_go()

    # 模拟交易
    def gogo(self, shard):
        for i in range(int(self.trans_interval / len(self.shards))):
            # shard.consensus_inter_non_sync()
            shard.consensus_inter()
            # shard.consensus_inter()
            time.sleep(random.uniform(0.03, 0.05))

    # 启动交易
    def start_go(self):
        for shard in self.shards:
            thr = threading.Thread(target=self.gogo, args=(shard,))
            thr.start()

    # 收集结果
    def gather_result(self, msg):
        cross_id = msg['cross_id']
        shard_id = msg['shard_id']
        data = msg['data']
        shard_num = msg['shard_num']
        index = self.find_gather(cross_id)
        if index == None:
            temp = [cross_id, data, set(), False]
            temp[2].add(shard_id)
            with self.lock_gether:
                self.gather.append(temp)
            logger.info(f' & ')
        else:
            with self.lock_gether:
                self.gather[index][2].add(shard_id)
            if len(list(self.gather[index][2])) >= calculate_tolerance(shard_num) + 1: # f + 1 就够确认
                if self.gather[index][3] == False:
                    with self.lock_gether:
                        # self.gather[index][2].clear()
                        self.gather[index][3] = True
                    # 添加片间共识结果
                    result = {'cross_id': self.gather[index][0],
                              'data': self.gather[index][1]}
                    self.add_consensus(result)
                    logger.info(f' $ ')

    def add_consensus(self, result):
        hash_object = hashlib.sha256()
        hash_object.update(msgpack.packb(result['cross_id']))
        if self.get_len() != 0:
            last_result = list(self.chain.queue)[-1]
            last_result_hash = last_result['hash_value']
            # 前后串联
            hash_object.update(msgpack.packb(last_result_hash))
        hash_value = hash_object.hexdigest()
        temp = {'hash_value': hash_value,
                'body': result
                }
        with self.lock:
            self.chain.put(temp)
            self.time_consensus.append(time.time())
        self.run_partition()

    # 获取区块数量
    def get_len(self):
        return self.chain.qsize()

    # 获取交易数量
    def get_trans_num(self):
        num = 0
        for temp in list(self.chain.queue):
            result = temp['body']
            data = result['data']
            num += len(data)
        return num

    # 打印信息
    def print_info(self):
        for temp in list(self.chain.queue):
            result = temp['body']
            print({'hash_value': temp['hash_value'],
                   'cross_id': result['cross_id'],
                   'data': result['data']})

    def find_gather(self, cross_id):
        index = 0
        for temp in self.gather:
            if temp[0] == cross_id:
                return index
            index += 1
        return None

    # 获得未共识区块
    # def get_False_consensus(self):
    #     false_consensus = [consensus for consensus in self.gather if consensus[3] == False]
    #     index = [index for index, consensus in enumerate(self.gather) if consensus[3] == False]
    #     with self.lock:
    #         for ind in index:
    #             self.gather[ind][3] = True
    #     return false_consensus

    # 重新分片后处理未完成区块
    # def process_flase(self, shards):
    #     with self.lock:
    #         false_consensus = self.get_False_consensus()
    #     if len(false_consensus) != 0:
    #         data = false_consensus[1]
    #         shard = random.choice(shards)
    #         peer = random.choice(shard.peers)
    #
    #         new_data = {'tag': 'ROUTE_pre-prepare',
    #                     'round': peer.round,
    #                     'shard_id': peer.shard_id,
    #                     'node_id': peer.node_id,
    #                     'block_id': false_consensus[0][3],
    #                     'data': data}
    #         router = random.choice(shard.router_addrs)
    #         peer.send_msg(new_data, router)



