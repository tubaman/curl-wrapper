import tempfile
import os
from .builder import execute_request

class Session:
    def __init__(self, curl_path='curl'):
        self.headers = {}
        self.curl_path = curl_path
        self._cookie_jar_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self._cookie_jar_file.close()
        self.cookie_jar = self._cookie_jar_file.name
    
    def _merge_kwargs(self, kwargs):
        merged = kwargs.copy()
        if 'headers' in merged:
            merged['headers'] = {**self.headers, **merged['headers']}
        else:
            merged['headers'] = self.headers.copy()
        merged['cookie_jar'] = self.cookie_jar
        merged['curl_path'] = self.curl_path
        return merged
    
    def close(self):
        if os.path.exists(self.cookie_jar):
            os.unlink(self.cookie_jar)
    
    def __del__(self):
        self.close()
    
    def get(self, url, **kwargs):
        return execute_request('GET', url, **self._merge_kwargs(kwargs))
    
    def post(self, url, **kwargs):
        return execute_request('POST', url, **self._merge_kwargs(kwargs))
    
    def put(self, url, **kwargs):
        return execute_request('PUT', url, **self._merge_kwargs(kwargs))
    
    def patch(self, url, **kwargs):
        return execute_request('PATCH', url, **self._merge_kwargs(kwargs))
    
    def delete(self, url, **kwargs):
        return execute_request('DELETE', url, **self._merge_kwargs(kwargs))
    
    def head(self, url, **kwargs):
        return execute_request('HEAD', url, **self._merge_kwargs(kwargs))
