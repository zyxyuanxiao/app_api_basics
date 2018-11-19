import os

from configs.base import *

flask_env = os.getenv('FLASK_ENV')
print('FLASK_ENV: %s' % flask_env)

if flask_env == "PROD":
    print('Loading config: PROD')
    from configs.prod import *
else:
    print('Loading config: DEV')
    from configs.dev import *