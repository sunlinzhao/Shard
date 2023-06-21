import threading
from socket import *
import msgpack
import logging
import time
import random
from concurrent.futures import ThreadPoolExecutor

from utils.MyUtils import get_free_port
from layer.DAG_Structure import DAG_Consensus

# 创建日志对象
logger = logging.getLogger()

class SyncNode(threading.Thread):
    def __init__(self, node_id, local_ip, local_port, shard_num):
        threading.Thread.__init__(self)
        self.daemon = True  # 设置为非守护线程，主线程等待子线程，子线程执行完毕后，主线才结束

        self.node_id = node_id
        self.local_ip = local_ip
        self.local_port = local_port
        self.shard_num = shard_num

        self.sync_addr_list = []

        self.BUF_LEN = 1024 * 64
        self.listen_num = 1000  # 应当设置的大一点，因为并行处理，可能出现线程的端口抢占

        self.global_state = []
        self.lock_global_state = threading.RLock()
        # DAG 平行链结构
        self.dag_global_state = DAG_Consensus(shard_num)
        self.lock_dag_global_state = threading.RLock()

        self.pool = ThreadPoolExecutor(1000)  # 线程池

        self.record_time = []
        # 记录共识时间
        self.time_consensus = []

    def run(self):
        # 创建socket
        listen_socket = self.create_socket(self.local_ip, self.local_port)
        # 进入监听状态
        listen_socket.listen(self.listen_num)

        # 写入日志,节点启动并监听
        logger.info(
            f'| - SyncNode [{self.node_id}] >>> listening on ({self.local_ip}:{self.local_port})')

        while True:
            # 返回的 dataSocket 用来通信、传输数据
            dataSocket, addr = listen_socket.accept()
            # logger.info(f'| Node [{self.node_id}] linked to {addr} !')
            self.pool.submit(self.handle_connect, dataSocket)

    def handle_connect(self, dataSocket):
        # 尝试读取对方发送的消息, BUF_LEN 指定从接收缓冲里最多读取多少字节。阻塞方式
        recved = dataSocket.recv(self.BUF_LEN)
        rec_msg = msgpack.unpackb(recved)
        self.pool.submit(self.excute, rec_msg)
        # 关闭客户端连接
        dataSocket.close()

    def excute(self, msg):
        if msg['tag'] == 'Query':
            self.pool.submit(self.process_Query, msg)
        if msg['tag'] == 'Record':
            self.pool.submit(self.process_Record, msg)
        if msg['tag'] == 'Sync_Query':
            self.pool.submit(self.process_Sync_Query, msg)
        if msg['tag'] == 'Sync':
            self.pool.submit(self.process_Sync, msg)
        if msg['tag'] == 'DAG_Query':
            self.pool.submit(self.process_DAG_Query, msg)
        if msg['tag'] == 'DAG_Record':
            self.pool.submit(self.process_DAG_Record, msg)
        if msg['tag'] == 'DAG_Sync_Query':
            self.pool.submit(self.process_DAG_Sync_Query, msg)
        if msg['tag'] == 'DAG_Sync':
            self.pool.submit(self.process_DAG_Sync, msg)

    def process_DAG_Sync_Query(self, msg):
        # print(f'count: {msg["count"]}')
        # 类gossip协议，先同步状态，如果状态存在就返回结果否则，继续同步
        self.pool.submit(self.dag_sync_state, msg['data'], msg['addr'])  # 同步消息
        is_know = random.choice([True] + [False]*(len(self.sync_addr_list)-1))  # 模拟查询，随机发起同步

        if msg['count'] >= len(self.sync_addr_list):
            is_know = True
            self.time_consensus.append(time.time())

        if is_know:
            raw_msg = msg['query_msg']
            send_data = {'tag': 'Response',
                         'round': raw_msg['round'],
                         'content': '',
                         'signal': raw_msg['signal'],
                         'addr': (self.local_ip, self.local_port)
                         }
            self.pool.submit(self.send_msg, send_data, raw_msg['addr'])
        else:
            data = [list(temp.chain.queue) for temp in self.dag_global_state.DAG_parallel]
            sync_query_data = {'tag': 'DAG_Sync_Query',
                               'query_msg': msg['query_msg'],
                               'data': data,
                               'addr': (self.local_ip, self.local_port),
                               'count': msg['count'] + 1
                               }
            # 随机向其他同步节点，发起同步查询
            self.pool.submit(self.send_msg, sync_query_data, random.choice(self.sync_addr_list))

    def process_DAG_Query(self, msg):
        # 收到查询消息，如果知道直接返回结果，否者发起同步节点同步请求
        is_know = random.choice([True] + [False]*(len(self.sync_addr_list)-1))  # 模拟查询，随机发起同步
        if is_know:
            send_data = {'tag': 'Response',
                         'round': msg['round'],
                         'content': '',
                         'signal': msg['signal'],
                         'addr': (self.local_ip, self.local_port)
                         }
            self.pool.submit(self.send_msg, send_data, msg['addr'])
        else:
            data = [list(temp.chain.queue) for temp in self.dag_global_state.DAG_parallel]
            sync_query_data = {'tag': 'DAG_Sync_Query',
                               'query_msg': msg,
                               'data': data,
                               'addr': (self.local_ip, self.local_port),
                               'count': 0
                               }
            # 随机向其他同步节点，发起同步查询
            self.pool.submit(self.send_msg, sync_query_data, random.choice(self.sync_addr_list))
            self.record_time.append(time.time())

    def process_DAG_Record(self, msg):
        shard_id = msg['shard_id']
        data = {'hash_value': msg['hash_value'],
                'block_id': msg['block_id'],
                'body': msg['body'],
                'self_parent': msg['self_parent'],
                'other_parent': msg['other_parent']
             }
        if data not in list(self.dag_global_state.DAG_parallel[shard_id].chain.queue):
            with self.lock_dag_global_state:
                self.dag_global_state.DAG_parallel[shard_id].chain.put(data)

    def process_Query(self, msg):
        # 收到查询消息，如果知道直接返回结果，否者发起同步节点同步请求
        is_know = random.choice([True, False])   # 模拟查询，随机发起同步
        if is_know:
            send_data = {'tag': 'Response',
                         'round': msg['round'],
                         'content': '',
                         'signal': msg['signal'],
                         'addr': (self.local_ip, self.local_port)
                         }
            self.pool.submit(self.send_msg, send_data, msg['addr'])
        else:
            sync_query_data = {'tag': 'Sync_Query',
                               'query_msg': msg,
                               'data': self.global_state,
                               'addr': (self.local_ip, self.local_port),
                               'count': 0
                               }
            # 随机向其他同步节点，发起同步查询
            self.pool.submit(self.send_msg, sync_query_data, random.choice(self.sync_addr_list))


    def process_Record(self, msg):
        raw_msg = msg['msg']
        info = [raw_msg['round'], raw_msg['shard_id'], raw_msg['node_id'], msg['number'], raw_msg['ID'], raw_msg['tag'],  msg['timestamp']]
        with self.lock_global_state:
            self.global_state.append(info)

    def process_Sync_Query(self, msg):
        # print(f'count: {msg["count"]}')
        # 类gossip协议，先同步状态，如果状态存在就返回结果否则，继续同步
        self.pool.submit(self.sync_state, msg['data'], msg['addr']) # 同步消息
        is_know = random.choice([True, False])  # 模拟查询，随机发起同步

        if msg['count'] > len(self.sync_addr_list):
            is_know = True

        if is_know:
            raw_msg = msg['query_msg']
            send_data = {'tag': 'Response',
                         'round': raw_msg['round'],
                         'content': '',
                         'signal': raw_msg['signal'],
                         'addr': (self.local_ip, self.local_port)
                         }
            self.pool.submit(self.send_msg, send_data, raw_msg['addr'])
        else:
            sync_query_data = {'tag': 'Sync_Query',
                               'query_msg': msg['query_msg'],
                               'data': self.global_state,
                               'addr': (self.local_ip, self.local_port),
                               'count': msg['count'] + 1
                               }
            # 随机向其他同步节点，发起同步查询
            self.pool.submit(self.send_msg, sync_query_data, random.choice(self.sync_addr_list))

    def process_Sync(self, msg):
        data = msg['data']
        with self.lock_global_state:
            # 同步状态
            self.global_state = list(set(self.global_state + data)) # 其实这里可以不用去重
            # self.global_state = self.global_state + data

    def process_DAG_Sync(self, msg):
        data = msg['data']
        with self.lock_dag_global_state:
            # 同步状态
            for i, chain in enumerate(data):
                for d in chain:
                    self.dag_global_state.DAG_parallel[i].chain.put(d)

    def dag_sync_state(self, data, addr):
        differences = []
        for i, chain in enumerate(data):
            difference = [temp for temp in list(self.dag_global_state.DAG_parallel[i].chain.queue) if temp not in set(chain)]  # 返回自己有而它没有的状态
            differences.append(difference)
        # 回复状态
        sync_data = {'tag': 'DAG_Sync',
                     'data': difference}
        self.pool.submit(self.send_msg, sync_data, addr)

        with self.lock_dag_global_state:
            # 同步状态
            for i, chain in enumerate(data):
                difference = [temp for temp in chain if temp not in set(list(self.dag_global_state.DAG_parallel[i].chain.queue))]  # 返回自己没有而它有的状态
                for d in difference:
                    self.dag_global_state.DAG_parallel[i].chain.put(d)

    def sync_state(self, data, addr):
        difference = [temp for temp in self.global_state if temp not in set(data)]  # 返回自己有而它没有的状态
        # 回复状态
        sync_data = {'tag': 'Sync',
                     'data': difference}
        self.pool.submit(self.send_msg, sync_data, difference)

        with self.lock_global_state:
            # 同步状态
            self.global_state = list(set(self.global_state + data))


    def create_socket(self, local_ip, local_port):
        # 实例化一个 socket 对象，指明TCP协议
        listenSocket = socket(AF_INET, SOCK_STREAM)
        # listenSocket.settimeout(5)  # 设置超时等待时间
        # socket 绑定地址和端口
        listenSocket.bind((local_ip, local_port))
        # 设置 SO_REUSEADDR 选项，以便在关闭连接后能够快速重新绑定相同的地址和端口号
        listenSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        return listenSocket

    def send_msg(self, msg, dest_addrs):
        # 序列化
        req_msg = msgpack.packb(msg)
        # 获取可用端口号
        free_port = get_free_port()
        # 生成 socket
        my_socket = self.create_socket(self.local_ip, free_port)
        # 建立连接
        my_socket.connect(tuple(dest_addrs))
        # 转发送给当前 leader
        my_socket.send(req_msg)

        time.sleep(0.01)
        # 假关闭，关闭写入和和可读通道
        my_socket.shutdown(SHUT_RDWR)
        # 关闭连接
        my_socket.close()
        time.sleep(random.uniform(0.001, 0.005))  # 防止太快，端口被占用完