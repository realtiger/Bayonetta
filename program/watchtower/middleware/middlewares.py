from watchtower.middleware.common import middleware as common_middleware
from watchtower.middleware.cors import middleware as cors_middleware

middlewares: list[dict] = []
middlewares.extend(common_middleware)
middlewares.extend(cors_middleware)
