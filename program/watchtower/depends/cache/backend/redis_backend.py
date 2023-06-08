from redis import asyncio as aioredis

from ....settings import settings


def create_conn_pool() -> aioredis.ConnectionPool:
    if settings.CACHE_REDIS_ENABLE:
        if settings.CACHE_REDIS_PASSWORD:
            if settings.CACHE_REDIS_USERNAME:
                redis_auth = f'{settings.CACHE_REDIS_USERNAME}:{settings.CACHE_REDIS_PASSWORD}@'
            else:
                redis_auth = f'{settings.CACHE_REDIS_PASSWORD}@'
        else:
            redis_auth = ''

        redis_url = f"redis://{redis_auth}{settings.CACHE_REDIS_HOST}:{settings.CACHE_REDIS_PORT}/{settings.CACHE_REDIS_DB}"
        return aioredis.ConnectionPool.from_url(redis_url, max_connections=100, decode_responses=True, encoding=settings.CACHE_REDIS_CHARSET)


pool = create_conn_pool()


def get_redis() -> aioredis.Redis:
    return aioredis.Redis(connection_pool=pool)
