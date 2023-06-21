import time
import random
import logging
import msgpack
import threading
from socket import *
from concurrent.futures import ThreadPoolExecutor
# 本地导入
from utils.MyUtils import get_free_port
from utils.Clock import LogicalClock

# 创建日志对象
logger = logging.getLogger()

# 模拟路由节点
class Router(threading.Thread):
    def __init__(self, node_id, local_ip, local_port, config):
        threading.Thread.__init__(self)
        self.daemon = True

        self.local_ip = local_ip
        self.local_port = local_port
        self.node_id = node_id
        self.config = config  # 片间共识结果收集确认


        self.shards = []
        self.BUF_LEN = 1024 * 16
        self.listen_num = 1000
        # 线程池
        self.pool = ThreadPoolExecutor(2000)
        self.lock = threading.RLock()

    # 启动
    def run(self):
        # 创建socket
        listen_socket = self.create_socket(self.local_ip, self.local_port)
        # 进入监听状态
        listen_socket.listen(self.listen_num)
        # 写入日志,节点启动并监听
        logger.info(
            f'| - Router [{self.node_id}] >>> listening on ({self.local_ip}:{self.local_port})')
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

    # 执行
    def excute(self, msg):
        if 'ROUTE' in msg['tag']:
            self.pool.submit(self.start_route, msg)
        if msg['tag'] == 'CONFIG':
            self.pool.submit(self.config_consensus, msg)
        if 'DAG' in msg['tag']:
            self.pool.submit(self.start_dag_route, msg)
            # print(msg)

    # 分片注册，添加分片
    def add_shard(self, shard):
        shard.router_addrs.append(tuple([self.local_ip, self.local_port]))
        self.shards.append(shard)

    # DAG 路由分发，路由给相关分片，验证通过则下一个产生的区块引用该区块
    def start_dag_route(self, msg):
        id = msg['shard_id']
        # 添加分片数量信息
        msg['shard_num'] = len(self.shards)
        shards = [shard for shard in self.shards if shard.shard_id != id]
        # 由于是模拟，所以随机选取一个相关分片
        shard = random.choice(shards)
        peer = random.choice(shard.peers)
        self.pool.submit(self.send_msg, msg, (peer.local_ip, peer.local_port))

    # 路由分发
    def start_route(self, msg):
        id = msg['shard_id']
        # 添加分片数量信息
        msg['shard_num'] = len(self.shards)
        for shard in self.shards:
            if id != shard.shard_id: # 不路由给发送者
                peer = random.choice(shard.peers)
                # self.send_msg(msg, (peer.local_ip, peer.local_port))
                self.pool.submit(self.send_msg, msg, (peer.local_ip, peer.local_port))
    # 片间共识结果收集确认
    def config_consensus(self, msg):
            self.config.gather_result(msg)

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
        # 发送
        my_socket.send(req_msg)

        time.sleep(0.01)
        # 假关闭，关闭写入和和可读通道
        my_socket.shutdown(SHUT_RDWR)
        # 关闭连接
        my_socket.close()
        time.sleep(random.uniform(0.001, 0.005))  # 防止太快，端口被占用完