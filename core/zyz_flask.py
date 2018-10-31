from flask import Blueprint

from core.system_constant import DEFAULT_METHODS

class ZyzBlueprint(Blueprint):
    def route(self,rule,**options):

        # 设置默认请求
        methods = options.get('methods')
        if not methods:
            options['methods'] = DEFAULT_METHODS

        def decorator(f):
            endpoint = options.pop("endpoint", f.__name__ + str(options.get('version')).replace('.','_'))
            self.add_url_rule(rule,endpoint.f,**options)
            return f

        return decorator