class CurlError(Exception):
    """Base exception for curl-related errors"""
    pass

class HTTPError(CurlError):
    """HTTP error (4xx, 5xx status codes)"""
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response

class Timeout(CurlError):
    """Request timeout"""
    pass
