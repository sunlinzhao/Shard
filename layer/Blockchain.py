import msgpack
import hashlib
import queue


class Block:
    def __init__(self):
        self.block_id = None
        self.other_parent = None
        self.self_parent = None
        self.data = []


    # 打印区块信息
    def print_block(self):
        # 只打印 交易的摘要信息
        digests = []
        for data in self.data:
            trans = msgpack.unpackb(data)
            digests.append(trans['digest'])
        info = {'block_id': self.block_id,
                'trans_info': digests
                }
        # print(info)
        return info

    # 获取区块包含的交易数量
    def get_len(self):
        return len(self.data)

    # 判断是否已经打包
    def is_packed(self):
        if self.block_id == None:
            return False
        else:
            return True
    # 判断是否为空
    def is_empty(self):
        if self.get_len() == 0:
            return True
        else:
            return False


    # 添加交易
    def add_trans(self, trans):
        if not self.is_packed():
            # 序列化，因为存在不可hash类型
            Tx = msgpack.packb(trans)
            self.data.append(Tx)
        else:
            print('block has packed !')

    # 判断区块内是否包含跨分片交易
    def is_inter(self):
        for data in self.data:
            trans = msgpack.unpackb(data)
            if trans['msg']['tag'] == 'INTER_ready':
                return True
        return False

# 模拟区块链
class BlockChain:
    def __init__(self, shard_id):
        self.shard_id = shard_id
        self.chain = queue.Queue()

    # 打印区块链信息
    def print_chain(self):
        for block in list(self.chain.queue):
            print({'shard_id': self.shard_id,
                   'hash_value': block['hash_value'],
                   'body': block['body']})

    # 获取区块链长度
    def get_len(self):
        return self.chain.qsize()

    def get_trans_num(self):
        num = 0
        for temp in list(self.chain.queue):
            block = temp['body']
            num += len(temp['body'])
        return num

    # 添加区块
    def add_block(self, block, flag, node):
        hash_object = hashlib.sha256()
        hash_object.update(msgpack.packb(block.block_id))
        if self.get_len() != 0:
            last_block = list(self.chain.queue)[-1]
            last_block_hash = last_block['hash_value']
            # 前后串联
            hash_object.update(msgpack.packb(last_block_hash))
            self_parent_id = last_block['block_id']
        else:
            self_parent_id = None
        hash_value = hash_object.hexdigest()
        temp = {'hash_value': hash_value,
                'block_id': block.block_id,
                'body': block.data,
                'self_parent': self_parent_id,
                'other_parent': block.other_parent
                }
        self.chain.put(temp)
        if flag == 'dag':
            # 给同步节点发送 dag 记录消息
            temp['tag'] = 'DAG_Record'
            temp['shard_id'] = node.shard_id
            node.pool.submit(node.send_msg, temp, node.shard.sync_addr)
