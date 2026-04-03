from .builder import execute_request

def get(url, **kwargs):
    return execute_request(url, **kwargs)

def post(url, **kwargs):
    return execute_request(url, method='POST', **kwargs)

def put(url, **kwargs):
    return execute_request(url, method='PUT', **kwargs)

def patch(url, **kwargs):
    return execute_request(url, method='PATCH', **kwargs)

def delete(url, **kwargs):
    return execute_request(url, method='DELETE', **kwargs)

def head(url, **kwargs):
    return execute_request(url, method='HEAD', **kwargs)
