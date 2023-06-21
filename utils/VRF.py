from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import pkcs1_15

import time


# 可验证随机函数的简单实现
def VRFgen():
    # 生成 RSA 密钥对
    rsa_key = RSA.generate(1024)
    sk = rsa_key.export_key()
    pk = rsa_key.publickey().export_key()
    return sk, pk

def VRFval(sk, x):
    # 创建 RSA 密钥对象
    rsa_key = RSA.import_key(sk)

    # 对输入进行哈希计算
    input_hash = SHA256.new(x.encode())

    # 创建数字签名对象
    signer = pkcs1_15.new(rsa_key)

    # 对输入进行数字签名
    signature = signer.sign(input_hash)

    return signature

def VRFprove(sk, x):
    # 创建 RSA 密钥对象
    rsa_key = RSA.import_key(sk)

    # 对输入进行哈希计算
    input_hash = SHA256.new(x.encode())

    # 创建数字签名对象
    signer = pkcs1_15.new(rsa_key)

    # 对输入进行数字签名
    signature = signer.sign(input_hash)

    return input_hash, signature

def VRFver(pk, x, val, proof):
    # 创建 RSA 密钥对象
    rsa_key = RSA.import_key(pk)

    # 对输入进行哈希计算
    input_hash = SHA256.new(x.encode())

    # 创建数字签名对象
    verifier = pkcs1_15.new(rsa_key)

    # 验证数字签名
    try:
        verifier.verify(input_hash, proof)
        return val == proof
    except (ValueError, TypeError):
        return False


if __name__ == '__main__':

    # 生成密钥对
    sk, pk = VRFgen()

    start = time.time()
    # 生成随机数输出
    x = "Hello, VRF!"
    val = VRFval(sk, x)

    # 计算零知识证明
    input_hash, proof = VRFprove(sk, x)
    end = time.time()

    # 验证随机数输出
    is_valid = VRFver(pk, x, val, proof)

    print("Secret Key (VRFSK):", sk)
    print("Public Key (VRFPK):", pk)
    print("Random Value (val):", val)
    print("Proof (proof):", proof)
    # print("input_hash:", input_hash)
    print("Is Valid:", is_valid)

    print(end - start)

