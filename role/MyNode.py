from concurrent.futures import ThreadPoolExecutor
from socket import *
import threading
import logging
import random
import time
import os
# 本地导入
from utils.MyUtils import get_free_port, generate_random_id, calculate_tolerance, count_connections
from layer.Blockchain import *
from utils.Clock import LogicalClock
from utils.VRF import *


# 创建日志对象
logger = logging.getLogger()
# 等待打包的间隔时间
WAIT_PACK = 3

class Node(threading.Thread):
    def __init__(self, local_ip, local_port):
        threading.Thread.__init__(self)
        self.daemon = True

        self.running = False

        self.local_ip = local_ip
        self.local_port = local_port

        # 无需传参的属性
        # 分片属性
        self.shard_id = None
        self.node_id = None # 分片内节点标识
        self.shard = None
        # 关于动态分片
        self.reputation = [None, None]    # 节点信誉值
        self.history_partition = []  # 历史分组记录列表
        self.round = 0  # 划分轮次
        # 节点属性
        self.sk , self.pk = VRFgen()    # 生成密钥对
        self.ID = generate_random_id()  # 节点唯一身份标识
        self.val = None
        self.proof = None

        self.n = 0
        self.v = 0

        self.BUF_LEN = 1024 * 16
        self.listen_num = 1000  # 应当设置的大一点，因为并行处理，可能出现线程的端口抢占

        self.peers = []  # 建立连接的节点
        self.rec_vn = []    # 相同 v_n 消息队列；分片内共识辅助数组
        self.vn_transaction = []    # vn 编号的区块

        self.pool = ThreadPoolExecutor(500) # 线程池

        self.lock_vn_transaction = threading.RLock() # 线程锁
        self.lock_rec_vn = threading.RLock()

        self.clock = LogicalClock(WAIT_PACK, self.packed_dag_block, args=()) # 逻辑时钟, 每间隔 3 秒做一次操作

    def run(self):
        self.running = True
        # 创建socket
        listen_socket = self.create_socket(self.local_ip, self.local_port)
        # 进入监听状态
        listen_socket.listen(self.listen_num)
        # 启动逻辑时钟
        self.clock.start()
        # 写入日志,节点启动并监听
        logger.info(f'| Shard [{self.shard_id}] : Node [{self.node_id}] >>> listening on ({self.local_ip}:{self.local_port})')
        while self.running:
            try:
                # 返回的 dataSocket 用来通信、传输数据
                dataSocket, addr = listen_socket.accept()
                # logger.info(f'| Node [{self.node_id}] linked to {addr} !')
                self.pool.submit(self.handle_connect, dataSocket)
            except Exception as e:
                if self.running:
                    logger.error(f"Node {self.node_id} encountered an error：{e}")
                break

    def stop(self):
        self.running = False
        self.serverSocket.close()
        self.pool.shutdown(wait=True)  # 等待当前任务完成
        logger.info(f"Node {self.node_id} stopped.")

    def handle_connect(self, dataSocket):
        # 尝试读取对方发送的消息, BUF_LEN 指定从接收缓冲里最多读取多少字节。阻塞方式
        recved = dataSocket.recv(self.BUF_LEN)
        rec_msg = msgpack.unpackb(recved)
        self.pool.submit(self.excute, rec_msg)
        # 关闭客户端连接
        dataSocket.close()

    def excute(self, msg):
        ''' ////////////////////////////////////////////////////////////////////////////////////////////////////////////
            片间共识
        '''
        if msg['tag'] == 'ROUTE_pre-prepare':
            self.pool.submit(self.process_ROUTE_pre_prepare, msg)
        if msg['tag'] == 'ROUTE_prepare':
            self.pool.submit(self.process_ROUTE_prepare, msg)
        if msg['tag'] == 'ROUTE_commit':
            self.pool.submit(self.process_ROUTE_commit, msg)
        if msg['tag'] == 'DAG_verify':
            self.pool.submit(self.process_DAG_verify, msg)

        ''' ////////////////////////////////////////////////////////////////////////////////////////////////////////////
            片内共识
        '''

        if msg['tag'] == 'Response':
            self.pool.submit(self.process_Response, msg)
        if msg['tag'] == 'INTRA' or msg['tag'] == 'INTER_ready':
            self.pool.submit(self.process_INTRA_INTER_ready, msg)
        if msg['tag'] == 'PRE_PREPARE':
            self.pool.submit(self.process_PRE_PREPARE, msg)
        if msg['tag'] == 'PREPARE':
            self.pool.submit(self.process_PREPARE, msg)
        if msg['tag'] == 'COMMIT':
            self.pool.submit(self.process_COMMIT, msg)

    def process(self, number, tag):
        index = self.find_vn(number)
        if index != None:
            q = self.rec_vn[index][1]
            if not q["pre-prepare"].empty() and tag=='pre-prepare':
                # print(q["pre-prepare"].get())
                pre_msg = q["pre-prepare"].get()
                self.broadcast(pre_msg)
                # self.pool.submit(self.broadcast, pre_msg)
            if not q['prepare'].empty() and tag=='prepare':
                prepare_msg = q["prepare"].get()
                self.broadcast(prepare_msg)
                # self.pool.submit(self.broadcast, prepare_msg)
            if not q['commit'].empty() and tag=='commit':
                commit_msg = q['commit'].get()
                self.broadcast(commit_msg)
                # self.pool.submit(self.broadcast, commit_msg)
        else:
            print(f'{number} is not exsit!')

    def process_cross(self, cross_id, tag):
        index = self.shard.find_cross_id(cross_id)
        if index != None:
            q = self.shard.cross_ids[index][1]
            if not q['prepare'].empty() and tag == 'ROUTE_prepare':
                cross_prepare = q['prepare'].get()
                # 路由到相关分片
                router = random.choice(self.shard.router_addrs)
                self.send_msg(cross_prepare, router)
                # self.pool.submit(self.send_msg, cross_prepare, router)
            if not q['commit'].empty() and tag == 'ROUTE_commit':
                cross_commit = q['commit'].get()
                # 路由到相关分片
                router = random.choice(self.shard.router_addrs)
                self.send_msg(cross_commit, router)
                # self.pool.submit(self.send_msg, cross_commit, router)
            if not q['config'].empty() and tag == 'CONFIG':
                cross_commit = q['config'].get()
                # 发给路由收集结果
                router = random.choice(self.shard.router_addrs)
                self.send_msg(cross_commit, router)
                # self.pool.submit(self.send_msg, cross_commit, router)

    def clear_queue(self, q):
        while not q.empty():
            item = q.get()

    def find_trans(self, number):
        index = 0
        for item in self.vn_transaction:
            if number == item[0]:
                return index
            index += 1
        return None

    def find_leader(self):
        for peer in self.peers:
            if peer.node_id == self.v % (len(self.peers) + 1) :
                return peer
        return None

    def find_vn(self, number):
        index = 0
        for item in self.rec_vn:
            if number == item[0]:
                return index
            index += 1
        return None

    def block_dag_route(self):
        # 获得分片内链上最新区块
        block = list(self.shard.blockchain.chain.queue)[-1]
        data = block['body']
        new_block = Block()
        new_block.data = data
        if new_block.is_inter():  # 判断区块内是否包含跨分片交易
            router = random.choice(self.shard.router_addrs)
            send_data = {'tag': 'DAG_verify',
                         'round': self.round,
                         'shard_id': self.shard_id,
                         'node_id': self.node_id,
                         'block_id': block['block_id'],
                         'data': data
                         }
            self.pool.submit(self.send_msg, send_data, router)

    def block_route(self):
        block = list(self.shard.blockchain.chain.queue)[-1]
        data = block['body']
        new_block = Block()
        new_block.data = data
        if new_block.is_inter():    # 判断区块内是否包含跨分片交易
            # 路由到其他分片
            router = random.choice(self.shard.router_addrs)
            send_data = {'tag': 'ROUTE_pre-prepare',
                         'round': self.round,
                         'shard_id': self.shard_id,
                         'node_id': self.node_id,
                         'block_id': block['block_id'],
                         'data': data
                         }
            # self.send_msg(send_data, router)
            self.pool.submit(self.send_msg, send_data, router)
            # cross_id = [send_data['round'], send_data['shard_id'], send_data['node_id'], send_data['block_id']]
            # index = self.shard.find_Tx_Pool(cross_id)
            # if index == None:
            #     self.shard.Tx_Pool.append([cross_id, send_data, False])
            # else:
            #     self.shard.Tx_Pool[index] = [cross_id, send_data, False]
            logger.info(f'###')

    def packed_dag_block(self):
        # 定时打包交易
        if self.node_id == self.v % (len(self.peers) + 1):
            false_list = [i for i, temp in enumerate(self.shard.wait_reference) if temp[1] == False]
            if len(false_list) != 0:
                with self.shard.lock_wait_reference:
                    self.shard.wait_reference[false_list[0]][1] = True
                parent_block_id = self.shard.wait_reference[false_list[0]][0]
            else:
                parent_block_id = None
            is_packed = self.shard.block.is_packed()
            is_empty = self.shard.block.is_empty()
            if (not is_packed) and (not is_empty):
                with self.shard.lock:
                    # 设置 block_id
                    self.shard.block.block_id = generate_random_id()
                    self.shard.block.other_parent = parent_block_id
                    # 添加到区块链
                    self.shard.blockchain.add_block(self.shard.block, 'dag', self)
                    # 区块重置
                    self.shard.block = Block()
                    self.block_dag_route()

    def packed_block(self):
        # 定时打包交易
        if self.node_id == self.v % (len(self.peers) + 1):
            is_packed = self.shard.block.is_packed()
            is_empty = self.shard.block.is_empty()
            if (not is_packed) and (not is_empty):
                with self.shard.lock:
                    # 设置 block_id
                    self.shard.block.block_id = generate_random_id()
                    # 添加到区块链
                    self.shard.blockchain.add_block(self.shard.block, 'non_dag', self)
                    # 区块重置
                    self.shard.block = Block()
                    self.block_route()

                    self.shard.time_consensus.append(time.time())

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
        try:
            # 获取可用端口号
            free_port = get_free_port()
            # 生成 socket
            my_socket = self.create_socket(self.local_ip, free_port)
            # 建立连接
            my_socket.connect(tuple(dest_addrs))
        except OSError:
            print(f'dest_addrs: {dest_addrs} - free_port: {(self.local_ip, free_port)}')
        my_socket.send(req_msg)
        # 假关闭，关闭写入和和可读通道
        my_socket.shutdown(SHUT_RDWR)
        time.sleep(0.01)
        # 关闭连接
        my_socket.close()
        time.sleep(random.uniform(0.01, 0.05))  # 防止太快，端口被占用完

    def broadcast(self, msg):
        # 序列化
        msg = msgpack.packb(msg)
        for peer in self.peers:
            # 获取可用端口号
            free_port = get_free_port()
            # 生成 socket
            my_socket = self.create_socket(self.local_ip, free_port)
            # 建立连接
            my_socket.connect((peer.local_ip, peer.local_port))
            # 发送消息
            my_socket.send(msg)

            time.sleep(0.01)
            # 假关闭，关闭写入和和可读通道
            my_socket.shutdown(SHUT_RDWR)
            # 关闭连接
            my_socket.close()
            time.sleep(random.uniform(0.01, 0.05))  # 防止太快，端口被占用完

    def process_DAG_verify(self, msg):
        if msg['round'] == self.round:  # 判断划分轮次
            if (self.v % (len(self.peers) + 1)) == self.node_id:  # 判断 Leader
                if True: # 模拟验证通过
                    with self.shard.lock_wait_reference:
                        self.shard.wait_reference.append([msg['block_id'], False])
                        # print(self.shard.wait_reference)
            else:
                # 转发 给 Leader
                leader = self.find_leader()
                if leader != None:
                    # self.send_msg(msg, (leader.local_ip, leader.local_port))
                    self.pool.submit(self.send_msg, msg, (leader.local_ip, leader.local_port))

    def process_ROUTE_pre_prepare(self, msg):
        if msg['round'] == self.round:  # 判断划分轮次
            if (self.v % (len(self.peers) + 1)) == self.node_id:  # 判断 Leader
                logger.info(
                    f'# Round [{self.round}] : Shard [{msg["shard_id"]}] : Node [{msg["node_id"]}] ----> Shard [{self.shard_id}] : Node [{self.node_id}] with {msg["tag"]} ')
                cross_id = [msg['round'], msg['shard_id'], msg['node_id'], msg['block_id']]
                # 生成消息
                cross_prepare = {'tag': 'ROUTE_prepare',
                                 'round': msg['round'],
                                 'cross_id': cross_id,
                                 'shard_id': self.shard_id,
                                 'ID': self.ID,
                                 'data': msg['data'],
                                 'shard_num': msg['shard_num']
                                 }
                index = self.shard.find_cross_id(cross_id)
                if index == None:
                    # 放入队列
                    q = {
                        "prepare": queue.Queue(),
                        "commit": queue.Queue(),
                        "config": queue.Queue(),
                    }
                    q["prepare"].put(cross_prepare)
                    with self.shard.lock:
                        self.shard.cross_ids.append([cross_id, q])
                else:
                    with self.shard.lock:
                        self.shard.cross_ids[index][1]["prepare"].put(cross_prepare)
                # 启动线程去处理
                self.pool.submit(self.process_cross, cross_id, 'ROUTE_prepare')
            else:
                # 转发 给 Leader
                leader = self.find_leader()
                if leader != None:
                    # self.send_msg(msg, (leader.local_ip, leader.local_port))
                    self.pool.submit(self.send_msg, msg, (leader.local_ip, leader.local_port))

    def process_ROUTE_prepare(self, msg):
        if msg['round'] == self.round:  # 判断划分轮次
            if (self.v % (len(self.peers) + 1)) == self.node_id:  # 判断 Leader
                cross_id = msg['cross_id']
                logger.info(
                    f'# Round [{self.round}] : Shard [{cross_id[0]}] : Node [{cross_id[1]}] ----> Shard [{self.shard_id}] : Node [{self.node_id}] with {msg["tag"]} ')
                index = self.shard.find_cross_id(cross_id)
                if index == None:
                    # 放入队列
                    q = {
                        "prepare": queue.Queue(),
                        "commit": queue.Queue(),
                        "config": queue.Queue(),
                    }
                    q["prepare"].put(msg)
                    with self.shard.lock:
                        self.shard.cross_ids.append([cross_id, q])
                else:
                    with self.shard.lock:
                        self.shard.cross_ids[index][1]["prepare"].put(msg)
                    wait_num = 2 * calculate_tolerance(msg['shard_num']) + 1
                    if self.shard.cross_ids[index][1]["prepare"].qsize() >= wait_num - 1:
                        with self.shard.lock:
                            self.clear_queue(self.shard.cross_ids[index][1]["prepare"])
                            # 生成消息
                            cross_commit = {'tag': 'ROUTE_commit',
                                            'round': msg['round'],
                                            'cross_id': cross_id,
                                            'shard_id': self.shard_id,
                                            'ID': self.ID,
                                            'data': msg['data'],
                                            'shard_num': msg['shard_num']
                                            }
                            # 放入消息队列
                            self.shard.cross_ids[index][1]["commit"].put(cross_commit)
                        # 启动线程去处理
                        self.pool.submit(self.process_cross, cross_id, 'ROUTE_commit')
            else:
                # 转发 给 Leader
                leader = self.find_leader()
                if leader != None:
                    # self.send_msg(msg, (leader.local_ip, leader.local_port))
                    self.pool.submit(self.send_msg, msg, (leader.local_ip, leader.local_port))

    def process_ROUTE_commit(self, msg):
        if msg['round'] == self.round:  # 判断划分轮次
            if (self.v % (len(self.peers) + 1)) == self.node_id:  # 判断 Leader
                cross_id = msg['cross_id']
                logger.info(
                    f'# Round [{self.round}] : Shard [{cross_id[0]}] : Node [{cross_id[1]}] ----> Shard [{self.shard_id}] : Node [{self.node_id}] with {msg["tag"]} ')
                index = self.shard.find_cross_id(cross_id)
                if index == None:
                    # 放入队列
                    q = {
                        "prepare": queue.Queue(),
                        "commit": queue.Queue(),
                        "config": queue.Queue(),
                    }
                    q["commit"].put(msg)
                    with self.shard.lock:
                        self.shard.cross_ids.append([cross_id, q])
                else:
                    with self.shard.lock:
                        self.shard.cross_ids[index][1]["commit"].put(msg)
                    wait_num = 2 * calculate_tolerance(msg['shard_num']) + 1
                    if self.shard.cross_ids[index][1]["commit"].qsize() >= wait_num - 1:
                        with self.shard.lock:
                            self.clear_queue(self.shard.cross_ids[index][1]["commit"])
                            # 生成消息 交给 router 节点去收集结果
                            cross_commit = {'tag': 'CONFIG',
                                            'round': msg['round'],
                                            'cross_id': cross_id,
                                            'shard_id': self.shard_id,
                                            'ID': self.ID,
                                            'data': msg['data'],
                                            'shard_num': msg['shard_num']
                                            }
                            # 放入消息队列
                            self.shard.cross_ids[index][1]["config"].put(cross_commit)
                        # 启动线程去处理
                        self.pool.submit(self.process_cross, cross_id, 'CONFIG')
                        # ind = self.shard.find_Tx_Pool(cross_id)
                        # if ind != None:
                        #     with self.shard.lock:
                        #         self.shard.Tx_Pool[ind][2] = True

            else:
                # 转发 给 Leader
                leader = self.find_leader()
                if leader != None:
                    # self.send_msg(msg, (leader.local_ip, leader.local_port))
                    self.pool.submit(self.send_msg, msg, (leader.local_ip, leader.local_port))

    def process_PRE_PREPARE(self, msg):
        if msg['round'] == self.round:  # 判断划分轮次
            number = msg['number']
            # 记录交易信息
            trans = {
                'tag': 'TRANS',
                'round': msg['round'],
                'number': msg['number'],
                'msg': msg['msg'],
                'digest': msg['digest'],
                'timestamp': msg['timestamp']
            }
            with self.lock_vn_transaction:
                self.vn_transaction.append((number, trans))

            logger.info(
                f'| Round [{self.round}] : Shard [{self.shard_id}] : Node [{self.v % (len(self.peers) + 1)}] ----> [{self.node_id}] with {msg["tag"]}    @  {number}')
            # 生成 PREPARE 消息包
            PREPARE = {'tag': 'PREPARE',
                       'round': msg['round'],
                       'number': number,
                       'digest': msg['digest'],
                       'addr': (self.local_ip, self.local_port),
                       'ID': self.ID,
                       'node_id': self.node_id
                       }
            index = self.find_vn(number)
            if index == None:  # 判断是否有已存在重复的编号
                # 放入队列
                q = {"pre-prepare": queue.Queue(),
                     "prepare": queue.Queue(),
                     "commit": queue.Queue(),
                     }
                q["prepare"].put(PREPARE)
                with self.lock_rec_vn:
                    self.rec_vn.append([number, q])
            else:
                with self.lock_rec_vn:
                    self.rec_vn[index][1]["prepare"].put(PREPARE)
            # 启动子线程处理器去处理 相同 number 的事务
            self.pool.submit(self.process, number, 'prepare')

    def process_PREPARE(self, msg):
        if msg['round'] == self.round:  # 判断划分轮次
            number = msg['number']
            logger.info(
                f'| Round [{self.round}] : Shard [{self.shard_id}] : Node [{msg["node_id"]}] ----> [{self.node_id}] with {msg["tag"]}        @  {number}')

            index = self.find_vn(number)
            if index == None:
                q = {"pre-prepare": queue.Queue(),
                     "prepare": queue.Queue(),
                     "commit": queue.Queue(),
                     }
                q["prepare"].put(msg)
                with self.lock_rec_vn:
                    self.rec_vn.append([number, q])
            else:
                with self.lock_rec_vn:
                    self.rec_vn[index][1]["prepare"].put(msg)
                wait_num = 2 * calculate_tolerance(len(self.peers) + 1) + 1
                if self.rec_vn[index][1]['prepare'].qsize() >= wait_num - 1:  # 收到大多数消息，包括自己的，所以减一
                    # 清空 prepare 消息队列
                    with self.lock_rec_vn:
                        self.clear_queue(self.rec_vn[index][1]['prepare'])
                    # 生成 COMMIT 消息包
                    COMMIT = {'tag': 'COMMIT',
                              'round': msg['round'],
                              'number': number,
                              'digest': msg['digest'],
                              'addr': (self.local_ip, self.local_port),
                              'ID': self.ID,
                              'node_id': self.node_id
                              }
                    # 放入消息队列
                    with self.lock_rec_vn:
                        self.rec_vn[index][1]["commit"].put(COMMIT)
                    # 启动子线程处理器去处理 相同 number 的事务
                    self.pool.submit(self.process, number, 'commit')

    def process_COMMIT(self, msg):
        if msg['round'] == self.round:  # 判断划分轮次
            number = msg['number']
            logger.info(
                f'| Round [{self.round}] : Shard [{self.shard_id}] : Node [{msg["node_id"]}] ----> [{self.node_id}] with {msg["tag"]}         @  {number}')
            index = self.find_vn(number)
            if index == None:
                q = {"pre-prepare": queue.Queue(),
                     "prepare": queue.Queue(),
                     "commit": queue.Queue(),
                     }
                q["commit"].put(msg)
                with self.lock_rec_vn:
                    self.rec_vn.append([number, q])
            else:
                with self.lock_rec_vn:
                    self.rec_vn[index][1]["commit"].put(msg)
                wait_num = 2 * calculate_tolerance(len(self.peers) + 1) + 1
                if self.rec_vn[index][1]['commit'].qsize() >= wait_num - 1:  # 收到大多数消息，包括自己的，所以减一
                    # 清空 commit 消息队列
                    with self.lock_rec_vn:
                        self.clear_queue(self.rec_vn[index][1]['commit'])
                    # 达成共识
                    index = self.find_trans(number)
                    if index != None:
                        trans = self.vn_transaction[index][1]
                        with self.shard.lock:
                            self.shard.add_trans(trans, self.node_id)
                    # 更新视图编号
                    self.v = self.v + 1


    def process_INTRA_INTER_ready(self, msg):
        if msg['round'] == self.round:  # 判断划分轮次
            # 如果是请求消息，则分配视图编号和消息编号，并加入消息队列
            if (self.v % (len(self.peers) + 1)) == self.node_id:  # 判断 Leader
                # 打包区块
                # if len(self.shard.block.data) >= BLOCK_SIZE:
                #     with self.shard.lock:
                #         # 设置 block_id
                #         self.shard.block.block_id = generate_random_id()
                #         # 添加到区块链
                #         self.shard.blockchain.add_block(self.shard.block, 'non_dag', self)
                #         # 区块重置
                #         self.shard.block = Block()
                #         self.block_route()

                # 分配编号
                number = [self.v, self.n]
                # 更新消息编号
                self.n = self.n + 1
                # 生成消息摘要
                sha256 = hashlib.sha256(msgpack.packb(msg))
                digest = sha256.hexdigest()
                # 生成 PRE-PREPARE 消息包
                PRE_PREPARE = {'tag': 'PRE_PREPARE',
                               'round': msg['round'],
                               'number': number,
                               'digest': digest,
                               'msg': msg,
                               'timestamp': time.time(),
                               'addr': (self.local_ip, self.local_port),
                               'ID': self.ID,
                               'node_id': self.node_id
                               }
                # 记录交易信息
                trans = {
                    'tag': 'TRANS',
                    'round': PRE_PREPARE['round'],
                    'number': PRE_PREPARE['number'],
                    'msg': PRE_PREPARE['msg'],
                    'digest': PRE_PREPARE['digest'],
                    'timestamp': PRE_PREPARE['timestamp']
                }
                with self.lock_vn_transaction:
                    self.vn_transaction.append((number, trans))

                index = self.find_vn(number)
                if index == None:  # 判断是否有已存在重复的编号
                    # 放入队列
                    q = {"pre-prepare": queue.Queue(),
                         "prepare": queue.Queue(),
                         "commit": queue.Queue(),
                         }
                    q["pre-prepare"].put(PRE_PREPARE)
                    with self.lock_rec_vn:
                        self.rec_vn.append([number, q])
                else:
                    with self.lock_rec_vn:
                        self.rec_vn[index][1]["pre-prepare"].put(PRE_PREPARE)
                # 启动子线程处理器去处理 相同 number 的事务
                self.pool.submit(self.process, number, 'pre-prepare')
            else:
                # 转发 给 Leader
                leader = self.find_leader()
                if leader != None:
                    # self.send_msg(msg, (leader.local_ip, leader.local_port))
                    self.pool.submit(self.send_msg, msg, (leader.local_ip, leader.local_port))

    def process_Response(self, msg):
        if msg['round'] == self.round:  # 判断划分轮次
            signal = msg['signal']
            index = self.shard.find_wait_confirmation(signal)
            if index != None:
                with self.shard.lock_wait_confirmation:
                    self.shard.wait_confirmation[index][2] = True
                    # print(len([temp for temp in self.shard.wait_confirmation if temp[2] == True]))
                    send_data = self.shard.wait_confirmation[index][1]

            if (self.v % (len(self.peers) + 1)) == self.node_id:  # 判断 Leader
                # self.process_INTRA_INTER_ready(send_data)
                self.pool.submit(self.process_INTRA_INTER_ready, send_data)
            else:
                # 给 Leader 发送交易发起共识
                leader = self.find_leader()
                if leader != None:
                    # self.send_msg(msg, (leader.local_ip, leader.local_port))
                    self.pool.submit(self.send_msg, send_data, (leader.local_ip, leader.local_port))

    def check(self, msg):
        # 假验证
        return True
