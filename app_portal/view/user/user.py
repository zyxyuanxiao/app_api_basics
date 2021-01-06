# -*-coding: utf-8-*-
from core.core import return_data,request_check
from app_portal import root, inner

@inner.route('/user/loginByMobile')
def Login_mobile():
    data = "hello world!!"
    return return_data(data=data,login_data={"user_id":"1234545"})
