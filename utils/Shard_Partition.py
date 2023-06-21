import math
import time
import concurrent.futures

# 本地导入
from layer.Gather import *
from layer.Shard import *
from utils.Monitor import Mointor
from role.MyNode import Node
from utils.VRF import *

# 动态划分轮次，动态分片
class Partitioning:
    def __init__(self, nodes, shards, monitor):
        self.nodes = nodes
        self.shards = shards
        self.monitor = monitor
        self.round = 0

    # 生成随机信誉值
    def generate_reputation(self):
        accuracy = self.monitor.get_accuracy()
        speed = self.monitor.get_speed()
        online = self.monitor.get_online()
        # 加权平均
        avs = []
        penaltys = []   # 惩罚因子
        repus = []  # 信誉值
        for i, node in enumerate(self.nodes):
            av = 0.6 * accuracy[i] + 0.2 * speed[i] + 0.2 * online[i]
            avs.append(av)
            if None in node.reputation:
                penalty = 0
            else:
                calculation = lambda x : x**3
                penalty = calculation(node.reputation[1] - node.reputation[0])

            penaltys.append(penalty)

            repu = (2*av / (av + math.exp(-10*penalty)))**3
            repu = float("{:.3f}".format(repu))
            repus.append(repu)
            # 节点更新信誉值
            node.reputation[0] = node.reputation[1]
            node.reputation[1] = repu
        return repus

    # 生成可验证随机函数值
    def generate_vrf(self):
        def get_val(node):
            val = VRFval(node.sk, str(node.round))
            node.val = val
            return val
        def get_proof(nodes):
            # 生成零知识证明
            _, proof = VRFprove(node.sk, str(node.round))
            node.proof = proof
            return proof

        all_vals = []
        all_proofs = []
        for node in self.nodes:
            # 以当前轮次字符作为所有节点都知道的输入值，与节点本身的私钥生成可验证的伪随机数
            all_vals.append(get_val(node))
            all_proofs.append(get_proof(node))
        return all_vals, all_proofs
    # 快速划分
    def divide_fast(self):
        # 获取hash分片编号
        def hash_id(level, ind, val, hashed, S):
            id = (val + ind) % S
            while id in hashed[level]:
                val = val + 1
                id = (val + ind) % S
            return id
        # 生产成信誉值
        self.generate_reputation()
        # 生成VRF
        self.generate_vrf()
        # 按信誉值排序
        sorted_nodes = sorted(self.nodes, key=lambda x: x.reputation[1], reverse=True)
        N = len(self.nodes)
        S = len(self.shards)

        l = N // S
        if N % S != 0:
            r = S + 1
        else:
            r = S

        hashed = [[] for i in range(r)]
        for i in range(N):
            level = (i // l) % r
            ''' verify the VRF '''
            if True:    # 此处验证随机值，省略
                ind = i - level * l
                id = hash_id(level, ind, int.from_bytes(self.nodes[i].val, byteorder='big'), hashed, S)
                self.shards[id].add_peer(self.nodes[i])
                self.nodes[i].clock.start()  # 启动计时打包器
                hashed[level].append(id)
        return hashed


    def divide(self):
        # 生产成信誉值
        self.generate_reputation()
        # 生成VRF
        self.generate_vrf()
        # 按信誉值排序
        sorted_nodes = sorted(self.nodes, key=lambda x: x.reputation[1], reverse=True)
        shard_num = len(self.shards)
        shard_size = len(sorted_nodes) // shard_num
        if len(sorted_nodes) % shard_num != 0:
            rank_num = shard_num + 1
        else:
            rank_num = shard_num

        # 未引入随机因素的划分
        rank_list = [[] for _ in range(rank_num)]
        for i, node in enumerate(sorted_nodes): # 按信誉值，划分等级
            rank_index = int(i / shard_size)
            rank_index = rank_index % rank_num
            rank_list[rank_index].append(node)

        divide_shard = [[] for _ in range(shard_num)]
        for rank in rank_list:
            # 此处省去对随机值的验证过程
            ''' verify the VRF '''
            # 按个节点的VRF随机值大小排序获得分片编号
            sorted_rank = sorted(rank, key=lambda x: int.from_bytes(x.val, byteorder='big'), reverse=True)
            for i, node in enumerate(sorted_rank):
                node.clock.start()  # 启动计时打包器
                self.shards[i].add_peer(node)
                divide_shard[i].append((node.reputation[1]))
        return divide_shard, rank_list


    # 划分分片
    def shard_partitioning(self):
        # 统一视图
        v_list = [node.v for node in self.nodes]
        v = max(v_list) + 1

        # 增加轮次
        self.round += 1

        # 清空分组
        for shard in self.shards:
            for node in shard.peers:
                node.clock.stop()   # 暂停计时打包器
                node.peers = []
                node.v = v  # 统一视图
                node.round = self.round # 统一轮次
            shard.peers = []

        # 划分分片
        self.divide_fast()

        logger.info(
                f'& >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Round [{self.round}] is running ! <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')


    # 打印分片
    def print_shards(self):
        for shard in self.shards:
            print(f"Shard {shard.shard_id}:")
            for node in shard.peers:
                print(f'Node - {node.ID}')
            print()
    # 打印各个节点的历史分组
    def print_history(self):
        # 打印节点的历史分组依据
        for node in self.nodes:
            print(f"Node {node.ID} 的历史分组：")
            print(node.history_partition)
            print()


if __name__ == '__main__':

    nodes = []
    for i in range(16):
        node = Node('127.0.0.1', 50000 + i)
        nodes.append(node)
    shards = []
    for i in range(4):
        shard = Shard(i)
        shards.append(shard)

    m = Mointor(nodes)
    p = Partitioning(nodes, shards, m)
    # for i in range(10):
    #     print(p.generate_reputation())
    #     time.sleep(1)

    # node1 = random.choice(nodes)
    # node1.round = 2

    # p.round = 2

    # vals, proofs = p.generate_vrf()
    # print(vals)
    # print(proofs)

    # verifys = []
    # for i, node in enumerate(p.nodes):
    #     verify = VRFver(node.pk, str(p.round), vals[i], proofs[i])
    #     verifys.append(verify)
    # print(verifys)

    # for node in nodes:
    #     print(int.from_bytes(node.val, byteorder='big') % 4)

    # p.shard_partitioning()
    # for shard in p.shards:
    #     for node in shard.peers:
    #         print(node.ID)
    # print()
    # p.shard_partitioning()
    # for shard in p.shards:
    #     for node in shard.peers:
    #         print(node.ID)

    print()
    start_time = time.time()
    hashed = p.divide_fast()
    end_time = time.time()
    print(hashed)
    print(end_time - start_time)
    # val = VRFval(nodes[6].sk, str(nodes[6].round))
    # print(int.from_bytes(val, byteorder='big'))

    # sorted_val = sorted(nodes, key=lambda x: int.from_bytes(x.val, byteorder='big'), reverse=True)
    # for node in sorted_val:
    #     print(int.from_bytes(node.val, byteorder='big'))
