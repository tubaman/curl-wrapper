class CurlError(Exception):
    """Base exception for curl-related errors"""
    pass


class HTTPError(CurlError):
    """HTTP error (4xx, 5xx status codes)"""
    def __init__(self, status, reason=None, response=None):
        message = f"HTTP {status}"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.status = status
        self.reason = reason
        self.response = response


class Timeout(CurlError):
    """Request timeout"""
    pass
