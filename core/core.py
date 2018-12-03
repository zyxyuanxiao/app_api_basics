import json
import datetime
import redis

from flask import make_response, request
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

from core.common import get_trace_id

from core.system_constant import REQUEST_FAIL, MOBILE_ORIGIN_URL
from configs import AUTH_COOKIE_AES_KEY, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD

class BaseError(object):
    def __init__(self):
        pass

    @staticmethod
    def not_login():
        data = json.dumps({
            'traceID': get_trace_id(),
            'code': 401,
            'msg': '用户未登录'
        })
        response = make_response(data,401)
        return response

    @staticmethod
    def request_params_incorrect():
        return return_data(code=REQUEST_FAIL, msg=u'请求参数不正确')


def return_data(code=200, data=None, msg=u'成功', login=None):
    data = {} if data is None else data
    data_json = json.dumps({'traceID': get_trace_id(),
                            'code': code,
                            'msg': msg,
                            'data': data})
    response = make_response(data_json, 200)
    response.headers['Content-Type'] = 'application/json'
    if request.headers.get('Origin') in MOBILE_ORIGIN_URL:
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin')
    else:
        response.headers['Access-Control-Allow-Origin'] = 'https://i.mofanghr.com'

    response.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    allow_headers = "Referer,Accept,Origin,User-Agent"
    response.headers['Access-Control-Allow-Headers'] = allow_headers
    create_auth_cookie(data, response, login)

    return response


def create_auth_cookie(data, response, login, cookie=None):
    cookie_info = {}

    if login is not None:
        if data is not None:
            user_id = data.get('userID')
            cookie_info['user_id'] = user_id

            outData = datetime.datetime.today() + datetime.timedelta(days=30)
            aes_crypt = AesCrypt(AUTH_COOKIE_AES_KEY)  # 初始化密钥



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


class Redis(object):
    REDIS_ = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    REDIS_1 = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    REDIS_2 = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    REDIS_3 = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    REDIS_4 = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

    REDIS_POOL_CACHE = {
        '0': REDIS_,
        '1': REDIS_1,
        '2': REDIS_2,
        '3': REDIS_3,
        '4': REDIS_4
    }

    def __init__(self, db=None):
        self.db = db

    def __get_pool(self):
        if self.db is None:
            self.db = '0'
        return self.REDIS_POOL_CACHE.get(self.db)

    def get_server(self):
        return redis.Redis(connection_pool=self.__get_pool())

    def set_variable(self, name, value, ex=None, px=None, nx=False, xx=False):
        # 设置普通键值对
        # EX — seconds – 设置键key的过期时间，单位时秒  （datetime.timedelta 格式）
        # PX — milliseconds – 设置键key的过期时间，单位时毫秒  （datetime.timedelta 格式）
        # NX – 只有键key不存在的时候才会设置key的值 （布尔值）
        # XX – 只有键key存在的时候才会设置key的值  （布尔值）
        self.get_server().set(name, value, ex, px, nx, xx)

    def get_variable(self, name):
        # 获取普通键值对的值
        return self.get_server().get(name)

    def delete_variable(self, *names):
        # 删除指定的一个或多个键 根据`names`
        self.get_server().delete(*names)

    def set_lpush(self, name, value):
        # 列表中增加值
        self.get_server().lpush(name, value)


    def srem_variable(self, name, *values):
        # 移除集合 key 中的一个或多个 member 元素，不存在的 member 元素会被忽略。
        return self.get_server().srem(name, *values)



