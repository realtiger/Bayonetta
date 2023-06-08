from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# from server.server import app

# 不安全url强制跳转安全url
# app.add_middleware(HTTPSRedirectMiddleware)
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"])
# minimum_size - 不压缩小宇这个字节数的响应，默认 500
# app.add_middleware(GZipMiddleware, )

middleware = [{
    "middleware_class": GZipMiddleware,
    "minimum_size": 1000
}]
