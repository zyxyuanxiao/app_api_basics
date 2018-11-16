
from flask_cors import CORS

import configs
from core.check_param import SubCheckParam, CheckParam
from core.zyz_flask import ZyzFlask, ZyzBlueprint

app = ZyzFlask(__name__)
app.config.from_object(configs)
CORS(app)


DEFAULT_METHODS = ['POST','GET']
check_param = CheckParam()


root = ZyzBlueprint('root', __name__)
inner = ZyzBlueprint('inner', __name__)
outer = ZyzBlueprint('outer', __name__)
manager = ZyzBlueprint('manager', __name__)
owner = ZyzBlueprint('owner', __name__)
member = ZyzBlueprint('member', __name__)
third = ZyzBlueprint('third', __name__)
offline = ZyzBlueprint('offline', __name__)


app.register_blueprint(root)
app.register_blueprint(inner, url_prefix='/inner')
app.register_blueprint(outer, url_prefix='/outer')
app.register_blueprint(manager, url_prefix='/manager')
app.register_blueprint(owner, url_prefix='/owner')
app.register_blueprint(member, url_prefix='/member')
app.register_blueprint(third, url_prefix='/third')
app.register_blueprint(offline, url_prefix='/offline')


check_root = SubCheckParam(DEFAULT_METHODS)
check_inner = SubCheckParam(DEFAULT_METHODS)
check_outer = SubCheckParam(DEFAULT_METHODS)
check_manager = SubCheckParam(DEFAULT_METHODS)
check_owner = SubCheckParam(DEFAULT_METHODS)
check_member = SubCheckParam(DEFAULT_METHODS)
check_third = SubCheckParam(DEFAULT_METHODS)

check_param.register_check_param(check_root)
check_param.register_check_param(check_inner, url_prefix='/inner')
check_param.register_check_param(check_outer, url_prefix='/outer')
check_param.register_check_param(check_manager, url_prefix='/manager')
check_param.register_check_param(check_owner, url_prefix='/owner')
check_param.register_check_param(check_member, url_prefix='/member')
check_param.register_check_param(check_third, url_prefix='/third')