from fastapi import status

from watchtower.depends.cache.backend.redis_backend import get_redis
from watchtower.settings import logger
from watchtower.status.global_status import StatusMap
from watchtower.status.types.exception import SiteException
from watchtower.status.types.response import GenericBaseResponse

CACHE_SYSTEM_EXCEPTION = SiteException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    response=GenericBaseResponse[dict](status=StatusMap.GET_CACHE_ERROR),
)


def get_permission_key(identify: str) -> str:
    return f'permission_{identify}'


def get_blacklist_key(identify: str) -> str:
    return f'blacklist_{identify}'


class CacheSystem:
    def __init__(self, backend):
        self.backend = backend

    def __call__(self):
        return self

    async def set_expire(self, key: str, expire: int):
        try:
            return await self.backend.expire(key, expire)
        except Exception as e:
            logger.error(f'set expire error: {e}')
            raise CACHE_SYSTEM_EXCEPTION from e

    async def get(self, key: str):
        try:
            return await self.backend.get(key)
        except Exception as e:
            logger.error(f'get cache error: {e}')
            raise CACHE_SYSTEM_EXCEPTION from e

    async def set(self, key: str, value: str, expire: int | None = None):
        try:
            return await self.backend.set(key, value, expire)
        except Exception as e:
            logger.error(f'set cache error: {e}')
            raise CACHE_SYSTEM_EXCEPTION from e

    async def delete(self, key: str):
        try:
            return await self.backend.delete(key)
        except Exception as e:
            logger.error(f'delete cache error: {e}')
            raise CACHE_SYSTEM_EXCEPTION from e

    async def hash_multi_set(self, key: str, mapping: dict):
        try:
            return await self.backend.hmset(key, mapping)
        except Exception as e:
            logger.error(f'hash multi set cache error: {e}')
            raise CACHE_SYSTEM_EXCEPTION from e

    async def hash_multi_get(self, key: str, fields: list):
        try:
            return await self.backend.hmget(key, fields)
        except Exception as e:
            logger.error(f'hash multi get cache error: {e}')
            raise CACHE_SYSTEM_EXCEPTION from e

    async def hash_delete(self, key: str, field: str | None = None):
        """
        删除hash表中的field
        :param key: 删除的key
        :param field: 删除的field，如果为None，则删除整个key
        :return:
        """
        try:
            if field is None:
                return await self.delete(key)
            return await self.backend.hdel(key, field)
        except Exception as e:
            logger.error(f'hash delete cache error: {e}')
            raise CACHE_SYSTEM_EXCEPTION from e

    # ##### 纯自定义，和项目耦合 #####
    async def set_permission(self, identify: int | str, permissions: dict, expire: int = 60):
        if len(permissions) == 0:
            return 'OK'
        permission_key = get_permission_key(str(identify))
        # 先删除原有的key，保证数据一致性，并且重新设置过期时间
        await self.hash_delete(permission_key)
        data = await self.hash_multi_set(permission_key, permissions)
        await self.set_expire(permission_key, expire)
        return data

    async def get_permission(self, identify: int | str, fields: list):
        return await self.hash_multi_get(get_permission_key(str(identify)), fields)

    async def delete_permission(self, identify: int | str):
        return await self.hash_delete(get_permission_key(str(identify)))

    async def set_blacklist(self, identify: int | str, value: str, expire: int = 60):
        return await self.set(get_blacklist_key(str(identify)), value, expire)

    async def get_blacklist(self, identify: int | str):
        return await self.get(get_blacklist_key(str(identify)))

    async def delete_blacklist(self, identify: int | str):
        return await self.delete(get_blacklist_key(str(identify)))


# TODO 目前只有redis，后续可以扩展
cache = CacheSystem(get_redis())
