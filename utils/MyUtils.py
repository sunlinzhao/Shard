import socket
import random
import uuid
import time
import threading
import psutil

def count_connections(port):
    count = 0

    # 获取系统中所有的网络连接信息
    connections = psutil.net_connections()

    # 遍历网络连接信息，计算指定端口的连接数量
    for conn in connections:
        if conn.status == 'ESTABLISHED' and conn.laddr.port == port:
            count += 1

    return count

def get_conn_ports():
    connections = psutil.net_connections()
    conn_ports = []

    for conn in connections:
        if conn.status == 'LISTEN':
            conn_ports.append(conn.laddr.port)

    return conn_ports

# 随机返回可用端口号
def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

# 生成随机 ID 与时间拼接
def generate_random_id():
    # 生成随机的UUID
    random_uuid = uuid.uuid4()
    # 获取当前时间戳
    current_timestamp = int(time.time())
    # 加强随机性
    char_list  = list(str(current_timestamp))
    random.shuffle(char_list)
    shuffled_string = ''.join(char_list)
    # 将UUID和时间戳进行拼接，得到最终的随机ID
    random_id = str(random_uuid) + '-' + str(current_timestamp) + '-' + shuffled_string

    return random_id

# 根据节点总数 N 计算 PBFT 容错率
def calculate_tolerance(N):
    if (N-1) % 3 == 0:
        return int((N-1) / 3)
    elif (N-1) % 3 == 1:
        return int((N-2) / 3)
    elif (N-1) % 3 == 2:
        return int(((N-3) / 3) + 1)
    else:
        return None

if __name__ == "__main__":
    print(generate_random_id())