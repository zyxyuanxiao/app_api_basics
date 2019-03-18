
import os
import uuid

from datetime import timedelta
from threading import Lock

from flask import Flask, Blueprint,cli
from flask.app import setupmethod
from flask.helpers import get_debug_flag, _PackageBoundObject, _endpoint_from_view_func
from flask.templating import _default_template_ctx_processor

from werkzeug.routing import Rule, Map, MapAdapter,RequestSlash, RequestRedirect, RequestAliasRedirect, _simple_rule_re
from werkzeug.urls import url_quote, url_join
from werkzeug.datastructures import ImmutableDict
from werkzeug._internal import _encode_idna, _get_environ
from werkzeug._compat import to_unicode, string_types, wsgi_decoding_dance
from werkzeug.exceptions import BadHost, NotFound, MethodNotAllowed



# 自定义flask蓝图,给所有路由增加'methods': ['GET', 'POST']参数。不用每个都写
class ZyzBlueprint(Blueprint):
    def __init__(self, name, import_name, default_methods=None,
                 static_folder=None,static_url_path=None, template_folder=None,
                 url_prefix=None, subdomain=None, url_defaults=None, root_path=None):

        super().__init__(name, import_name, static_folder=static_folder,
                         static_url_path=static_url_path, template_folder=template_folder,
                         url_prefix=url_prefix, subdomain=subdomain, url_defaults=url_defaults,
                         root_path=root_path)

        self.default_methods = default_methods

    # 装饰器
    def route(self,rule,**options):

        # 设置默认请求
        methods = options.get('methods')
        if not methods:
            options['methods'] = self.default_methods

        # 给函数名增加版本号，多个版本使用相同函数名时，蓝图存储监听时可以区分。
        def decorator(f):
            endpoint = options.pop("endpoint", f.__name__ + str(options.get('version')).replace('.','_'))
            # add_url_rule 函数，就是将路由和函数名的对应关系，生成一个flask对象，存在Blueprint类中的deferred_functions类属性中
                # rule： 路由 例：/userInfo/get.json
                # endpoint : 函数名，自定义加上了版本号 例：login_mobile['3_1_2']
                # f ： 函数 例：<function sheng_portal.backend.view.versions.version_1_3_1.controller.user.user.login_check>
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
        'ENV': None,
        'DEBUG': get_debug_flag(), # 启用/禁用调试模式
        'TESTING': False, # 启用/禁用测试模式
        'PROPAGATE_EXCEPTIONS': None, # 显式地允许或禁用异常的传播。如果没有设置或显式地设置为 None ，当 TESTING 或 DEBUG 为真时，这个值隐式地为 true.
        'PRESERVE_CONTEXT_ON_EXCEPTION': None, # 你同样可以用这个设定来强制启用（允许调试器内省），即使没有调试执行，这对调试生产应用很有用（但风险也很大）
        'SECRET_KEY': None, # 密匙 还不知道干嘛用的
        'PERMANENT_SESSION_LIFETIME': timedelta(days=31), # 控制session的过期时间
        'USE_X_SENDFILE': False, # 启用/禁用 x-sendfile（一种下载文件的工具），打开后，下载不可控，可能有漏洞，需谨慎
        'SERVER_NAME': None, # 服务器名和端口。需要这个选项来支持子域名 （例如： 'myapp.dev:5000' ）
        'APPLICATION_ROOT': '/',  # 如果应用不占用完整的域名或子域名，这个选项可以被设置为应用所在的路径。这个路径也会用于会话 cookie 的路径值。如果直接使用域名，则留作 None
        'SESSION_COOKIE_NAME': 'session', # 会话 cookie 的名称。
        'SESSION_COOKIE_DOMAIN': '.mofanghr.com', # 会话 cookie 的域。如果不设置这个值，则 cookie 对 SERVER_NAME 的全部子域名有效
        'SESSION_COOKIE_PATH': '/', # 会话 cookie 的路径。如果不设置这个值，且没有给 '/' 设置过，则 cookie 对 APPLICATION_ROOT 下的所有路径有效
        'SESSION_COOKIE_HTTPONLY': True, # 控制 cookie 是否应被设置 httponly 的标志， 默认为 True
        'SESSION_COOKIE_SECURE': False, # 控制 cookie 是否应被设置安全标志，默认为 False
        'SESSION_REFRESH_EACH_REQUEST': True, # 如果被设置为 True （这是默认值），每一个请求 cookie 都会被刷新。如果设置为 False ，只有当 cookie 被修改后才会发送一个 set-cookie 的标头
        'MAX_CONTENT_LENGTH': None, # 如果设置为字节数， Flask 会拒绝内容长度大于此值的请求进入，并返回一个 413 状态码
        'SEND_FILE_MAX_AGE_DEFAULT': timedelta(hours=12), # 默认缓存控制的最大期限，以秒计，
        'TRAP_BAD_REQUEST_ERRORS': None, # 这个设置用于在不同的调试模式情形下调试，返回相同的错误信息 BadRequest
        'TRAP_HTTP_EXCEPTIONS': False, # 如果这个值被设置为 True ，Flask不会执行 HTTP 异常的错误处理
        'EXPLAIN_TEMPLATE_LOADING': False, # 解释模板加载
        'PREFERRED_URL_SCHEME': 'http', # 生成URL的时候如果没有可用的 URL 模式话将使用这个值。默认为 http
        'JSON_AS_ASCII': True, # 默认情况下 Flask 使用 ascii 编码来序列化对象。如果这个值被设置为 False ， Flask不会将其编码为 ASCII，并且按原样输出，返回它的 unicode 字符串
        'JSON_SORT_KEYS': True, #　Flask 按照 JSON 对象的键的顺序来序来序列化它。这样做是为了确保键的顺序不会受到字典的哈希种子的影响，从而返回的值每次都是一致的，不会造成无用的额外 HTTP 缓存
        'JSONIFY_PRETTYPRINT_REGULAR': False, # 如果这个配置项被 True （默认值）， 如果不是 XMLHttpRequest 请求的话（由 X-Requested-With 标头控制） json 字符串的返回值会被漂亮地打印出来。
        'JSONIFY_MIMETYPE': 'application/json',
        'TEMPLATES_AUTO_RELOAD': None,
        'SESSION_COOKIE_SAMESITE':'Lax',  # SameSite限制如何使用来自外部站点的请求发送cookie。可以设置为“lax”（推荐）或“strict”。LAX防止从外部站点（如提交表单）发送带有易受CSRF影响的请求的cookie。strict禁止发送带有所有外部请求的cookie，包括以下常规链接。
        'MAX_COOKIE_SIZE': 4093, # cookie 最大容量
    })
    def __init__(
            self,
            import_name,
            static_url_path=None,
            static_folder='static',
            static_host=None,
            host_matching=False,
            subdomain_matching=False,
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
        if static_url_path is not None:
            self.static_url_path = static_url_path
        if static_folder is not None:
            self.static_folder = static_folder
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
        self.error_handler_spec = {}

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
        #:    view = Flask(__name__)
        #:    view.url_map.converters['list'] = ListConverter
        #：   @list.route("/job.json")  >>> /list/job.json
        self.url_map = ZyzMap()

        self.url_map.host_matching = host_matching
        self.subdomain_matching = subdomain_matching

        # 如果应用程序已经处理至少一个，则在内部跟踪
        self._got_first_request = False
        self._before_request_lock = Lock()

        #  使用提供的静态URL路径、静态主机和静态文件夹添加静态路由
        if self.has_static_folder:
            assert bool(static_host) == host_matching, 'Invalid static_host/host_matching combination'
            self.add_url_rule(
                self.static_url_path + '/<path:filename>',
                endpoint='static',
                host=static_host,
                view_func=self.send_static_file
            )
        self.cli = cli.AppGroup(self.name)

    def create_url_adapter(self, request):
        if request is not None:
            # 设置 request_id
            request.trace_id = str(uuid.uuid4())
            # 设置 view version
            request.version = get_version(request)
            # 如果禁用子域匹配（默认），则在所有情况下都使用默认子域。
            subdomain = ((self.url_map.default_subdomain or None)
                         if not self.subdomain_matching else None)

            return self.url_map.bind_to_environ(request.environ, request=request,
                                                version_dict=self.version_dict,
                                                server_name=self.config['SERVER_NAME'],
                                                subdomain=subdomain )
        # 我们至少需要设置服务器名才能使其正常工作
        if self.config['SERVER_NAME'] is not None:
            return self.url_map.bind(
                self.config['SERVER_NAME'],
                script_name=self.config['APPLICATION_ROOT'] or '/',
                url_scheme=self.config['PREFERRED_URL_SCHEME']
            )

    @setupmethod
    def add_url_rule(self, rule, endpoint=None, view_func=None, provide_automatic_options=None, **options):
        if endpoint is None:
            endpoint = _endpoint_from_view_func(view_func)
        options['endpoint'] = endpoint
        methods = options.pop('methods', None)

        if methods is None:
            methods = getattr(view_func,'methods',None) or ('GET',)
        if isinstance(methods, string_types):
            raise TypeError('Allowed methods have to be iterables of strings, '
                            'for example: @app.route(..., methods=["POST"])')
        methods = set(item.upper() for item in methods)

        # 应始终添加的方法
        required_methods = set(getattr(view_func, 'required_methods', ()))

        if provide_automatic_options is None:
            provide_automatic_options = getattr(view_func,
                'provide_automatic_options', None)

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
    def bind(self, server_name, script_name=None, subdomain=None,
             url_scheme='http', default_method='GET', path_info=None,
             query_args=None, request=None, version_dict=None):
        server_name = server_name.lower()
        if self.host_matching:
            if subdomain is not None:
                raise RuntimeError('host matching enabled and a '
                                   'subdomain was provided')
            elif subdomain is None:
                subdomain = self.default_subdomain
        if script_name is None:
            script_name = '/'
        try:
            server_name = _encode_idna(server_name)
        except UnicodeError:
            raise BadHost()
        return ZyzMapAdapter(self,server_name, script_name, subdomain,
                             url_scheme, path_info, default_method,
                             query_args, request, version_dict)

    def bind_to_environ(self, environ, server_name=None, subdomain=None, request=None, version_dict=None):
        environ = _get_environ(environ)

        if 'HTTP_HOST' in environ:
            wsgi_server_name = environ['HTTP_HOST']

            if environ['wsgi.url_scheme'] == 'http' and wsgi_server_name.endswith(':80'):
                wsgi_server_name = wsgi_server_name[:-3]
            elif environ['wsgi.url_scheme'] == 'https' and wsgi_server_name.endswith(':443'):
                wsgi_server_name = wsgi_server_name[:-4]
        else:
            wsgi_server_name = environ['SERVER_NAME']

            if (environ['wsgi.url_scheme'],environ['SERVER_PORT']) not in (('https','443'),('http','80')):
                wsgi_server_name += ':' + environ['SERVER_PORT']

        wsgi_server_name = wsgi_server_name.lower()

        if server_name is None:
            server_name = wsgi_server_name
        else:
            server_name = server_name.lower()

        if subdomain is None and not self.host_matching:
            cur_server_name = wsgi_server_name.split('.')
            real_server_name = server_name.split('.')
            offset = -len(real_server_name)
            if cur_server_name[offset:] != real_server_name:
                subdomain = '<invalid>'
            else:
                subdomain = '.'.join(filter(None, cur_server_name[:offset]))
        def _get_wsgi_string(name):
            val = environ.get(name)
            if val is not None:
                return wsgi_decoding_dance(val, self.charset)

        script_name = _get_wsgi_string('SCRIPT_NAME')
        path_info = _get_wsgi_string('PATH_INFO')
        query_args = _get_wsgi_string('QUERY_STRING')
        return ZyzMap.bind(self, server_name, script_name,
                              subdomain, environ['wsgi.url_scheme'],
                              environ['REQUEST_METHOD'], path_info,
                              query_args=query_args, request=request, version_dict=version_dict)

class ZyzMapAdapter(MapAdapter):
    def __init__(self, map, server_name, script_name, subdomain,
                 url_scheme, path_info, default_method, query_args=None,
                 request=None, version_dict=None):
        self.request = request
        self.version_dict = version_dict if version_dict is not None else {}
        super().__init__(map, server_name, script_name, subdomain, url_scheme,
                         path_info, default_method, query_args)
    def match(self, path_info=None, method=None, return_rule=False,
              query_args=None):
        self.map.update()
        if path_info is None:
            path_info = self.path_info
        else:
            path_info = to_unicode(path_info, self.map.charset)
        if query_args is None:
            query_args = self.query_args
        method = (method or self.default_method).upper()

        path = u'%s|%s' % (
            self.map.host_matching and self.server_name or self.subdomain,
            path_info and '/%s' % path_info.lstrip('/')
        )

        have_match_for = set()
        for rule in self.map._rules:
            try:
                rv = rule.match(path, method)
            except RequestSlash:
                raise RequestRedirect(self.make_redirect_url(
                    url_quote(path_info, self.map.charset,
                              safe='/:|+') + '/', query_args))
            except RequestAliasRedirect as e:
                raise RequestRedirect(self.make_alias_redirect_url(
                    path, rule.endpoint, e.matched_values, method, query_args))
            if rv is None:
                continue
            if rule.methods is not None and method not in rule.methods:
                have_match_for.update(rule.methods)
                continue

            # 确定版本
            version = get_version(self.request)
            if self.request and version:
                if not isinstance(rule.version, list) or not rule.version:
                    rule.version = list()

                version_list = self.version_dict.get(rule.rule)

                if len(rule.version) == 0 \
                        and version_list is not None \
                        and version in version_list:
                    continue
                elif len(rule.version) != 0 and version not in rule.version:
                    continue
            self.request.rule_version = rule.version

            if self.map.redirect_defaults:
                redirect_url = self.get_default_redirect(rule, method, rv, query_args)

                if redirect_url is not None:
                    raise RequestRedirect(redirect_url)

            if rule.redirect_to is not None:
                if isinstance(rule.redirect_to, string_types):
                    def _handle_match(match):
                        value = rv[match.group(1)]
                        return rule._converters[match.group(1)].to_url(value)
                    redirect_url = _simple_rule_re.sub(_handle_match,
                                                       rule.redirect_to)
                else:
                    redirect_url = rule.redirect_to(self, **rv)
                raise RequestRedirect(str(url_join('%s://%s%s%s' % (
                    self.url_scheme or 'http',
                    self.subdomain and self.subdomain + '.' or '',
                    self.server_name,
                    self.script_name
                ), redirect_url)))

            if return_rule:
                return rule, rv
            else:
                return rule.endpint, rv
        if have_match_for:
            raise MethodNotAllowed(valid_methods=list(have_match_for))
        raise NotFound()

def get_version(request):
    try:
        return request.version
    except AttributeError:
        pass
    return request.args.get('version')
