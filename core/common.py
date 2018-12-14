import uuid

from flask import request

def get_trace_id():
    try:
        if request.trace_id is None:
            return uuid.uuid1()
        else:
            return request.trace_id
    except Exception:
        return uuid.uuid1()

def is_none(arg):
    return not arg or str(arg) in ['null','none','false']

def get_version(request):
    try:
        return request.version
    except AttributeError:
        pass
    return request.args.get('version')
