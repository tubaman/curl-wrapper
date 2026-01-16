from .builder import execute_request

def get(url, **kwargs):
    return execute_request('GET', url, **kwargs)

def post(url, **kwargs):
    return execute_request('POST', url, **kwargs)

def put(url, **kwargs):
    return execute_request('PUT', url, **kwargs)

def patch(url, **kwargs):
    return execute_request('PATCH', url, **kwargs)

def delete(url, **kwargs):
    return execute_request('DELETE', url, **kwargs)

def head(url, **kwargs):
    return execute_request('HEAD', url, **kwargs)
