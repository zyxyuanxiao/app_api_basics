import random
import string
import hashlib

from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

def get_randoms(num):
    ran_str = ''.join(random.sample(string.ascii_letters + string.digits, num))
    return ran_str


def get_hashlib(text):
    return hashlib.sha1(text).hexdigest()


class AesCrypt(object):
    def __init__(self,key):
        self.key = key
        self.iv = key
        self.mode = AES.MODE_CBC  # CBC模式是目前公认AES中最安全的加密模式

    # 加密函数，如果text不是16的倍数【加密文本text必须为16的倍数！】，那就补足为16的倍数
    def encrypt(self,text):
        cipher = AES.new(self.key, self.mode, self.iv) # 参数（密钥，加密模式，偏移量）
        # 这里密钥key 长度必须为16（AES-128）、24（AES-192）、或32（AES-256）Bytes 长度.目前AES-128足够用
        length = 16
        add = length - (len(text) % length)
        text = text + ('\0' * add)
        self.ciphertext = cipher.encrypt(text)
        # 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
        # 所以这里统一把加密后的字符串转化为16进制字符串 ,当然也可以转换为base64加密的内容，可以使用b2a_base64(self.ciphertext)
        return b2a_hex(self.ciphertext)

    def decrypt(self,text):
        cipher = AES.new(self.key, self.mode, self.iv)
        plain_text = cipher.decrypt(a2b_hex(text))
        return plain_text.rstrip('\0') # 删掉后面补位用的‘\0’
