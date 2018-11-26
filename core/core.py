import json
import datetime

from flask import make_response, request

from core.common import get_trace_id
from core.system_constant import REQUEST_FAIL, MOBILE_ORIGIN_URL

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