import math
import struct
import hashlib
import binascii
from Crypto.PublicKey import RSA

'''
from: https://blog.csdn.net/weixin_34112900/article/details/92178673
'''

k = hashlib.sha1().digest_size

def rsasp1(K, m):
    if not (0 <= m <= K['n'] - 1):
        raise Exception("message representative out of range")

    return pow(m, K['d'], K['n'])


def rsavp1(K, s):
    if not (0 <= s <= K['n'] - 1):
        raise Exception("message representative out of range")

    return pow(s, K['e'], K['n'])


def i2osp(x):
    '''
        将非负整数转换为八位字节字符串
    '''

    try:

        return struct.pack('I', x)

    except:

        return binascii.unhexlify(len(hex(x)[2:]) % 2 * '0' + hex(x)[2:])


def os2ip(x):
    '''
        将八位字节字符串转换为非负整数
    '''
    return int(binascii.hexlify(x), 16)


def mgf1(mgf_seed, mask_len, Hash=hashlib.sha1):
    '''

    Options:
        Hash: hash function (hLen denotes the length in octets ofthe hash function output)
        Input:
            mgfSeed - seed from which mask is generated,an octet string
            maskLen - intended length in octets of the mask, at most 2^32 hLen
        Output:
            mask - mask, an octet string of length maskLen
        Error:"mask too long"
        Hash默认算法是SHA1
    '''

    T = b''

    for i in range(math.ceil(mask_len / Hash().digest_size)):
        C = i2osp(i)

        T = T + Hash(mgf_seed.encode() + C).digest()

    return T[:mask_len]


def rsafdhvrf_prove(K, alpha):
    '''
    Input:
        K - RSA private key
        alpha - VRF hash input, an octet string
    Output:
        pi - proof, an octet string of length k
    '''
    EM = mgf1(alpha, k - 1)

    m = os2ip(EM)

    s = rsasp1(K, m)

    pi = i2osp(s)

    return pi


def rsafdhvrf_proof2hash(pi, Hash=hashlib.sha1):
    beta = Hash(pi).digest()

    return beta


def rsafdhvrf_verify(K, alpha, pi):
    s = os2ip(pi)

    m = rsavp1(K, s)

    EM = i2osp(m)

    EM_ = mgf1(alpha, k - 1)

    if EM == EM_:

        return "VALID"

    else:

        return "INVALID"


alpha = 'hello word'

rsa = RSA.generate(1024)

K = {'e': rsa.e, 'n': rsa.n, 'd': rsa.d}

pi = rsafdhvrf_prove(K, alpha)

print(rsa)

beta = rsafdhvrf_proof2hash(pi)

result = rsafdhvrf_verify(K, alpha, pi)

print(result)
