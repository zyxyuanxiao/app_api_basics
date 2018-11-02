from flask import Flask, Blueprint
from flask.helpers import get_debug_flag

from werkzeug.routing import Rule
from werkzeug.datastructures import ImmutableDict

from core.system_constant import DEFAULT_METHODS

# 自定义flask蓝图,给所有路由增加'methods': ['GET', 'POST']参数。不用每个都写
class ZyzBlueprint(Blueprint):
    # 装饰器
    def route(self,rule,**options):

        # 设置默认请求
        methods = options.get('methods')
        if not methods:
            options['methods'] = DEFAULT_METHODS

        # 给函数名增加版本号，多个版本使用相同函数名时，蓝图存储监听时可以区分。
        def decorator(f):
            endpoint = options.pop("endpoint", f.__name__ + str(options.get('version')).replace('.','_'))
            # add_url_rule 函数，就是将路由和函数名的对应关系，生成一个flask对象，存在Blueprint类中的deferred_functions类属性中
                # rule： 路由 例：/userInfo/get.json
                # endpoint : 函数名，自定义加上了版本号 例：login_mobile['3_1_2']
                # f ： 函数 例：<function sheng_portal.backend.app.versions.version_1_3_1.controller.user.user.login_check>
                # **options : 路由后面带的参数 例{'methods': ['GET', 'POST'], 'version': ['1.3.1']}
            self.add_url_rule(rule, endpoint, f, **options)
            return f

        return decorator


class ZyzRule(Rule):
    def __init__(self, string, version=None, **options):
        self.version = version
        super().__init__(string, **options)


class ZyzFlask(Flask):
    url_rule_class = ZyzRule

    # 默认设置，配置参数
    default_config = ImmutableDict({
        'DEBUG': get_debug_flag(), # 启用/禁用调试模式
        'TESTING': False, # 启用/禁用测试模式
        'PROPAGATE_EXCEPTIONS': None,
        'preserve_context_on_exception': None,
        'secret_key': None,
    })