from fastapi.middleware.cors import CORSMiddleware

from watchtower.settings import settings

# 解决跨域问题
middleware = [{
    "middleware_class": CORSMiddleware,
    "allow_origins": settings.CORS_ALLOW_ORIGINS,
    "allow_origin_regex": settings.CORS_ALLOW_ORIGIN_REGEX,
    "allow_credentials": settings.CORS_ALLOW_CREDENTIALS,
    "allow_methods": settings.CORS_ALLOW_METHODS,
    "allow_headers": settings.CORS_ALLOW_HEADERS,
    "expose_headers": settings.CORS_EXPOSE_HEADERS,
    "max_age": settings.CORS_MAX_AGE,
}]
