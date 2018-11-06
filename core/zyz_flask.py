
import os
import uuid

from datetime import timedelta
from threading import Lock

from flask import Flask, Blueprint,cli
from flask.helpers import get_debug_flag, _PackageBoundObject, _endpoint_from_view_func
from flask.templating import _default_template_ctx_processor

from werkzeug.routing import Rule,Map
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
        'PROPAGATE_EXCEPTIONS': None, # 显式地允许或禁用异常的传播。如果没有设置或显式地设置为 None ，当 TESTING 或 DEBUG 为真时，这个值隐式地为 true.
        'PRESERVE_CONTEXT_ON_EXCEPTION': None, # 你同样可以用这个设定来强制启用（允许调试器内省），即使没有调试执行，这对调试生产应用很有用（但风险也很大）
        'SECRET_KEY': None, # 密匙 还不知道干嘛用的
        'PERMANENT_SESSION_LIFETIME': timedelta(days=31), # 控制session的过期时间
        'USE_X_SENDFILE': False, # 启用/禁用 x-sendfile（一种下载文件的工具），打开后，下载不可控，可能有漏洞，需谨慎
        'LOGGER_NAME': None, # 日志记录器的名称
        'LOGGER_HANDLER_POLICY': 'always', # 可以通过配置这个来组织flask默认记录日志
        'SERVER_NAME': None, # 服务器名和端口。需要这个选项来支持子域名 （例如： 'myapp.dev:5000' ）
        'APPLICATION_ROOT': None,  # 如果应用不占用完整的域名或子域名，这个选项可以被设置为应用所在的路径。这个路径也会用于会话 cookie 的路径值。如果直接使用域名，则留作 None
        'SESSION_COOKIE_NAME': 'session', # 会话 cookie 的名称。
        'SESSION_COOKIE_DOMAIN': '.mofanghr.com', # 会话 cookie 的域。如果不设置这个值，则 cookie 对 SERVER_NAME 的全部子域名有效
        'SESSION_COOKIE_PATH': '/', # 会话 cookie 的路径。如果不设置这个值，且没有给 '/' 设置过，则 cookie 对 APPLICATION_ROOT 下的所有路径有效
        'SESSION_COOKIE_HTTPONLY': True, # 控制 cookie 是否应被设置 httponly 的标志， 默认为 True
        'SESSION_COOKIE_SECURE': False, # 控制 cookie 是否应被设置安全标志，默认为 False
        'SESSION_REFRESH_EACH_REQUEST': True, # 如果被设置为 True （这是默认值），每一个请求 cookie 都会被刷新。如果设置为 False ，只有当 cookie 被修改后才会发送一个 set-cookie 的标头
        'MAX_CONTENT_LENGTH': None, # 如果设置为字节数， Flask 会拒绝内容长度大于此值的请求进入，并返回一个 413 状态码
        'SEND_FILE_MAX_AGE_DEFAULT': timedelta(hours=12), # 默认缓存控制的最大期限，以秒计，
        'TRAP_BAD_REQUEST_ERRORS': False, # 这个设置用于在不同的调试模式情形下调试，返回相同的错误信息 BadRequest
        'TRAP_HTTP_EXCEPTIONS': False, # 如果这个值被设置为 True ，Flask不会执行 HTTP 异常的错误处理
        'EXPLAIN_TEMPLATE_LOADING': False, # 解释模板加载
        'PREFERRED_URL_SCHEME': 'http', # 生成URL的时候如果没有可用的 URL 模式话将使用这个值。默认为 http
        'JSON_AS_ASCII': True, # 默认情况下 Flask 使用 ascii 编码来序列化对象。如果这个值被设置为 False ， Flask不会将其编码为 ASCII，并且按原样输出，返回它的 unicode 字符串
        'JSON_SORT_KEYS': True, #　Flask 按照 JSON 对象的键的顺序来序来序列化它。这样做是为了确保键的顺序不会受到字典的哈希种子的影响，从而返回的值每次都是一致的，不会造成无用的额外 HTTP 缓存
        'JSONIFY_PRETTYPRINT_REGULAR': True, # 如果这个配置项被 True （默认值）， 如果不是 XMLHttpRequest 请求的话（由 X-Requested-With 标头控制） json 字符串的返回值会被漂亮地打印出来。
        'JSONIFY_MIMETYPE': 'application/json',
        'TEMPLATES_AUTO_RELOAD': None,
    })

    def __init__(
            self,
            import_name,
            static_path=None,
            static_url_path=None,
            static_folder='static',
            template_folder='templates',
            instance_path=None,
            instance_relative_config=False,
            root_path=None
        ):
        self.version_dict = {}

        _PackageBoundObject.__init__(
            self,
            import_name,
            template_folder=template_folder,
            root_path=root_path
        )

        if static_path is not None:
            from warnings import warn
            warn(DeprecationWarning('static_path is now called static_url_path'),
                 stacklevel=2)
            static_url_path = static_path
        if static_url_path is not None:
            self.static_url_path = static_url_path
        if static_folder is not None:
            self.static_floder = static_folder
        if instance_path is None:
            instance_path = self.auto_find_instance_path()
        elif not os.path.isabs(instance_path):
            raise ValueError('If an instance path is provided it must be '
                             'absolute. A relative path was given instead.')

        # 保存实例文件夹的路径。  versionadded:: 0.8
        self.instance_path = instance_path

        # 这种行为就像普通字典，但支持其他方法从文件加载配置文件。
        self.config = self.make_config(instance_relative_config)

        # 准备记录日志的设置
        self._logger = None
        self.logger_name = self.import_name

        # 注册所有视图函数的字典。钥匙会是：用于生成URL的函数名值是函数对象本身。
        # 注册一个视图函数，使用：route装饰器
        self.view_functions = {}

        # 支持现在不推荐的Error处理程序属性。现在将使用
        self._error_handlers = {}

        #: A dictionary of all registered error handlers.  The key is ``None``
        #: for error handlers active on the application, otherwise the key is
        #: the name of the blueprint.  Each key points to another dictionary
        #: where the key is the status code of the http exception.  The
        #: special key ``None`` points to a list of tuples where the first item
        #: is the class for the instance check and the second the error handler
        #: function.
        #:
        #: To register a error handler, use the :meth:`errorhandler`
        #: decorator.
        self.error_handler_spec = {None: self._error_handlers}

        #: A list of functions that are called when :meth:`url_for` raises a
        #: :exc:`~werkzeug.routing.BuildError`.  Each function registered here
        #: is called with `error`, `endpoint` and `values`.  If a function
        #: returns ``None`` or raises a :exc:`BuildError` the next function is
        #: tried.
        #:
        #: .. versionadded:: 0.9
        self.url_build_error_handlers = []

        self.before_request_funcs = {}

        self.before_first_request_funcs = []

        self.after_request_funcs = {}

        self.teardown_request_funcs = {}

        self.teardown_appcontext_funcs = []

        self.url_value_preprocessors = {}

        self.url_default_functions = {}

        self.template_context_processors = {
            None: [_default_template_ctx_processor]
        }

        self.shell_context_processor = []

        self.blueprints = {}
        self._blueprint_order = []

        self.extensions = {}

        # 使用这个可以在创建类之后改变路由转换器的但是在任何线路连接之前
        #     from werkzeug.routing import BaseConverter
        #:    class ListConverter(BaseConverter):
        #:        def to_python(self, value):
        #:            return value.split(',')
        #:        def to_url(self, values):
        #:            return ','.join(BaseConverter.to_url(value)
        #:                            for value in values)
        #:
        #:    app = Flask(__name__)
        #:    app.url_map.converters['list'] = ListConverter
        #：   @list.route("/job.json")  >>> /list/job.json
        self.url_map = ZyzMap()

        # 如果应用程序已经处理至少一个，则在内部跟踪
        self._got_first_request = False
        self._before_request_lock = Lock()

        if self.has_static_folder:
            self.add_url_rule(self.static_url_path + '/<path:filename>',
                              endpoint='static',
                              view_func=self.send_static_file)
        self.cli = cli.AppGroup(self.name)

    def make_config(self, instance_relative=False):
        """用于通过flask构造函数创建config属性。从构造函数传递“nstance_relative”参数
        flask（名为“instance_relative_config”），并指示是否配置应该与实例路径或
        根路径相对应。"""
        root_path = self.root_path
        if instance_relative:
            root_path = self.instance_path
        return self.config_class(root_path, self.default_config)

    def create_url_adapter(self, request):
        if request is not None:
            # 设置 request_id
            request.trace_id = str(uuid.uuid4())
            # 设置 app version
            request.version = self.get_version(request)

            return self.url_map.bind_to_environ(request.environ, request=request,
                                                version_dict=self.version_dict,
                                                server_name=self.config['SERVER_NAME'])
        if self.config['SERVER_NAME'] is not None:
            return self.url_map.bind(
                self.config['SERVER_NAME'],
                script_name=self.config['APPLICATION_ROOT'] or '/',
                url_scheme=self.config['PREFERRED_URL_SCHEME']
            )

    def get_version(self,request):
        try:
            return request.version
        except AttributeError:
            pass
        return request.args.get('version')

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        if endpoint is None:
            endpoint = _endpoint_from_view_func(view_func)
        options['endpoint'] = endpoint
        methods = options.pop('methods', None)

        if methods is None:
            methods = getattr(view_func,'methods',None) or ('GET',)
        methods = set(methods)

        required_methods = set(getattr(view_func, 'required_methods', ()))

        provide_automatic_options = getattr(view_func,
                                            'provide_automatic_options',
                                            None)
        if provide_automatic_options is None:
            if "OPTIONS" not in methods:
                provide_automatic_options = True
                required_methods.add('OPTIONS')
            else:
                provide_automatic_options = False

        # 设置 version_dict
        if self.version_dict.get(rule) is None:
            self.version_dict[rule] = []

        version_list = self.version_dict.get(rule.strip())

        # 添加version list
        version = options.get('version')
        if version and isinstance(version, list):
            for item in version:
                if item not in version_list:
                    version_list.append(item)

        # 增加回调时 的 methods
        methods |= required_methods

        rule = self.url_rule_class(rule, methods=methods, **options)
        rule.provide_automatic_options = provide_automatic_options

        self.url_map.add(rule)
        if view_func is not None:
            old_func = self.view_functions.get(endpoint)
            if old_func is not None and old_func != view_func:
                raise AssertionError('View function mapping is overwriting an '
                                     'existing endpoint function: %s' % endpoint)

            self.view_functions[endpoint] = view_func

class ZyzMap(Map):
    pass

