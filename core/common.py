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