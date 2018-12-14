import time
import json
import datetime
import redis
import hashlib

from flask import make_response, request

from configs import *
from core.utils import get_randoms, AesCrypt, get_hashlib
from core.common import get_trace_id, is_none, get_version

from core.global_settings import REQUEST_FAIL, MOBILE_ORIGIN_URL

from configs import AES_KEY, REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, AUTH_COOKIE_KEY

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



class Redis(object):
    def __init__(self,db=None):
        self.db = db
        if not hasattr(Redis,'REDIS_POOL_CACHE'):
           self.getRedisCoon()
        self.get_server()

    def getRedisCoon(self):
        REDIS_ = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
        REDIS_1 = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=1)
        REDIS_2 = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=2)
        REDIS_3 = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=3)
        REDIS_4 = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=4)

        self.REDIS_POOL_CACHE = {
            '0': REDIS_,
            '1': REDIS_1,
            '2': REDIS_2,
            '3': REDIS_3,
            '4': REDIS_4
        }

    def __get_pool(self):
        if self.db is None:
            self.db = '0'
        return self.REDIS_POOL_CACHE.get(self.db)

    def get_server(self):
        self.conn = redis.Redis(connection_pool=self.__get_pool())
        return self.conn

    def set_variable(self, name, value, ex=None, px=None, nx=False, xx=False):
        # 设置普通键值对
        # EX — seconds – 设置键key的过期时间，单位时秒  （datetime.timedelta 格式）
        # PX — milliseconds – 设置键key的过期时间，单位时毫秒  （datetime.timedelta 格式）
        # NX – 只有键key不存在的时候才会设置key的值 （布尔值）
        # XX – 只有键key存在的时候才会设置key的值  （布尔值）
        self.conn.set(name, value, ex, px, nx, xx)

    def get_variable(self, name):
        # 获取普通键值对的值
        return self.conn.get(name)

    def delete_variable(self, *names):
        # 删除指定的一个或多个键 根据`names`
        self.conn.delete(*names)

    def get_hget(self, name, key):
        return self.conn.hget(name, key)

    def get_hgetall(self, name):
        return self.conn.hgetall(name)

    def set_hset(self, name, key, value):
        self.conn.hset(name, key, value)

    def set_rpush(self, name, value):
        # 列表结尾中增加值
        self.conn.rpush(name, value)

    def get_lpop(self, name):
        # 弹出列表的第一个值（非阻塞）
        self.conn.lpop(name)

    def set_blpop(self, *name, timeout=0):
        # 弹出传入所有列表的第一个有值的（阻塞），可以设置阻塞超时时间
        self.conn.blpop(*name, timeout)

    def get_llen(self, name):
        # 返回列表的长度（列表不存在时返回0）
        self.conn.llen(name)

    def set_sadd(self, name, value):
        # 集合中增加元素
        self.conn.sadd(name, value)

    def delete_srem(self, name, *value):
        # 删除集合中的一个或多个元素
        self.conn.srem(name, *value)

    def spop(self, name):
        # 随机移除集合中的一个元素并返回
        return self.get_server().spop(name)

    def smembers(self, name):
        return self.conn.smembers(name)

    def sismember(self, name, value):
        # 判断value是否是集合name中的元素。是返回1 ，不是返回0
        return self.conn.sismember(name,value)

    def expire(self,name,time):
        # 设置key的过期时间
        self.conn.expire(name,time)


class LoginAndReturn(object):
    def __init__(self):
        pass


def login_required_one(f):
    @wraps(f)
    def decorated_function(*args, **kw):
        #### 所有注释都是进行单点登录操作的 !!!!!!!
        auth_token = request.cookies.get('app_auth_token')
        refresh_time = request.cookies.get('app_refresh_time')

        if auth_token is None and refresh_time is None:
            return BaseError.not_local_login()

        aes_crypt = AesCrypt(AES_KEY)  # 初始化密钥
        auth_token = aes_crypt.decrypt(auth_token)

        user_id = get_user_id_by_cookie_new(auth_token) # 这个个方法里存在单点登录状态

        only_code = get_only_code_by_cookie(auth_token)

        # 去redis中取 组装cookie时存的随机数
        _redis = Redis()
        _only_code = _redis.get_hget("app_only_code", user_id)

        user_id = get_user_id_by_cookie(auth_token)

        if user_id is None or user_id == 'None':
            return BaseError.not_login()

        # 校验cookie解析出来的随机数 和存在redis中的随机数是否一致
        if _only_code and only_code != _only_code:
            logger.info("账号在其他设备登陆了%s"% user_id)
            return BaseError.not_local_login()

        # 利用user_id + '#$%' + redis中随机数 + '#$%' + md5加密后的字符串 组装auth_token
        auth_cookie = hashlib.sha1(AUTH_COOKIE_KEY + user_id + refresh_time).hexdigest()
        if auth_token == auth_cookie:
            return f(*args, **kw)
        else:
            return BaseError.not_login()

    return decorated_function

# 制作response并返回的函数,包括制作response的请求头和请求体
#   login_data : 登录操作时必传参数，必须包括userID，其余可以包括想带入cookie中的参数 格式{“userID”:“12345”}
def return_data(code=200, data=None, msg=u'成功', login_data=None):
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
    response.headers['Access-Control-Allow-Headers'] = "Referer,Accept,Origin,User-Agent"
    create_auth_cookie(response, login_data)

    return response


def create_auth_cookie(response, login_data):
    # 进场获取缓存cookie中的信息
    auth_token = request.cookies.get('auth_token')
    refresh_time = request.cookies.get('refresh_time') # refresh_time = 1482222171524
    cookie_info = request.cookies.get('cookie_info')

    # 设置cookie过期时间点， time.time() + 60 表示一分钟后
    outdate = time.time() + 60 * 60 * 24 * 3  # 记录登录态三天
    user_id = None

    #login 如果是登录操作，cookie中所有信息重新生成
    if not is_none(login_data)  and not is_none(login_data.get('userID')):
        user_id = login_data.get('userID')

        sso_code = "vJjPtawUC8" # 如果当前版本不设置单点登录，则使用固定随机码
        if get_version(request) in SSO_VERSION:
            # 如果版本设置单点登录,随机生成10位随机数，当做单机唯一登录码，存在redis中方便对比
            # 只要不清除登录态，单点登录则不会触发
            sso_code = get_randoms(10)
            _redis = Redis()
            _redis.set_hset("app_sso_code", user_id, sso_code)

        # 产生新的refresh_time 和新的auth_token
        refresh_time = str(int(round(time.time() * 1000)))
        sign_str = get_hashlib(AUTH_COOKIE_KEY + user_id + refresh_time + sso_code)
        auth_token = aes_crypt_encrypt(AUTH_COOKIE_KEY + sign_str)
        cookie_info = aes_crypt_encrypt(json.dumps(login_data))


    #not login 如果不是登录操作，并且cookie中auth_token和refresh_time存在
    if not is_none(auth_token) and  not is_none(refresh_time):
        now_time = int(round(time.time() * 1000))
        differ_minuts = (now_time - int(refresh_time)) / (60*1000)

        if differ_minuts >= 30 and is_none(login_data):
            user_id = get_info_by_authToken(auth_token).get('user_id')
            sso_code = get_info_by_authToken(auth_token).get('sso_code') #获取单点登录码


            if not is_none(user_id):
                refresh_time = str(int(round(time.time() * 1000)))
                auth_token = generate_token(user_id, refresh_time,sso_code)

                response.set_cookie('auth_token', auth_token)
                response.set_cookie('refresh_time', str(refresh_time))

    return response


def get_sign(auth_token):
    if auth_token is not None:
        auth_tokens = auth_token.split(AUTH_COOKIE_KEY)
        if len(auth_tokens) == 2:
            return auth_tokens[0]
    return None


# 使用AES算法对字符串进行加密
def aes_crypt_encrypt(text):
    aes_crypt = AesCrypt(AES_KEY)  # 初始化密钥
    encrypt = aes_crypt.encrypt(text) # 加密字符串
    return encrypt