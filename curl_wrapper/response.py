import json as json_lib

class Response:
    def __init__(self, status_code, headers, body, url, history=None):
        self.status_code = status_code
        self.headers = headers
        self._body = body
        self.url = url
        self.history = history or []
    
    @property
    def content(self):
        return self._body
    
    @property
    def text(self):
        if isinstance(self._body, bytes):
            encoding = self._get_encoding()
            return self._body.decode(encoding, errors='replace')
        return self._body
    
    def _get_encoding(self):
        content_type = self.headers.get('content-type', '').lower()
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1].split(';')[0].strip()
            return charset
        return 'utf-8'
    
    def json(self):
        return json_lib.loads(self.text)
    
    def raise_for_status(self):
        from .exceptions import HTTPError
        if 400 <= self.status_code < 600:
            raise HTTPError(self.status_code, response=self)
