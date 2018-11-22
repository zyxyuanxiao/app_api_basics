import json

class BaseError(object):
    def __init__(self):
        pass

    @staticmethod
    def not_login():
        data = json.dump({
            'traceID': get_trace_id()
        })


def get_trace_id():
