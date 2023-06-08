from fastapi import status

from .backend.redis_backend import get_redis
from ... import StatusMap
from ...status.types.exception import SiteException
from ...status.types.response import GenericBaseResponse

CACHE_SYSTEM_EXCEPTION = SiteException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    response=GenericBaseResponse[dict](status=StatusMap.GET_CACHE_ERROR),
)


class CacheSystem:
    def __init__(self, backend):
        self.backend = backend

    def __call__(self):
        return self

    async def get(self, key: str):
        try:
            return await self.backend.get(key)
        except Exception as e:
            raise CACHE_SYSTEM_EXCEPTION from e

    async def set(self, key: str, value: str, expire: int | None = None):
        try:
            return await self.backend.set(key, value, expire)
        except Exception as e:
            raise CACHE_SYSTEM_EXCEPTION from e

    # ##### 纯自定义，和项目耦合 #####
    async def set_permission(self, identify: str, value: str = "all", expire: int = 60):
        key = f'permission_{identify}'
        return await self.set(key, value, expire)


# TODO 目前只有redis，后续可以扩展
cache = CacheSystem(get_redis())
