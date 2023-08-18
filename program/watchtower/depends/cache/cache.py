import json

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


def get_menu_key(identify: str = None) -> str:
    if identify is None:
        return 'global_menu'
    return f'menu_{identify}'


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

    async def hash_get(self, key: str, field: str):
        try:
            return await self.backend.hget(key, field)
        except Exception as e:
            logger.error(f'hash get cache error: {e}')
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
    async def set_permission(self, identify: int | str, permissions: dict, expire: int = 60, encode: bool = True):
        if len(permissions) == 0:
            return 'OK'

        if encode:
            permissions = {k: json.dumps(v) for k, v in permissions.items()}

        permission_key = get_permission_key(str(identify))
        # 先删除原有的key，保证数据一致性，并且重新设置过期时间
        await self.hash_delete(permission_key)
        data = await self.hash_multi_set(permission_key, permissions)
        await self.set_expire(permission_key, expire)
        return data

    async def get_permission(self, identify: int | str, fields: list | str, decode: bool = True):
        if not fields:
            return None

        if isinstance(fields, str):
            permissions = await self.hash_get(get_permission_key(str(identify)), fields)
            if decode and permissions:
                permissions = json.loads(permissions)
        else:
            permissions = await self.hash_multi_get(get_permission_key(str(identify)), fields)
            if decode and permissions:
                permissions = [json.loads(p) if p else None for p in permissions]

        # permissions 是一个 list[{ 'id': int, 'url': str, 'code': str}] 格式的数据
        return permissions

    async def delete_permission(self, identify: int | str):
        return await self.hash_delete(get_permission_key(str(identify)))

    async def set_blacklist(self, identify: int | str, value: str, expire: int = 60):
        return await self.set(get_blacklist_key(str(identify)), value, expire)

    async def get_blacklist(self, identify: int | str):
        return await self.get(get_blacklist_key(str(identify)))

    async def delete_blacklist(self, identify: int | str):
        return await self.delete(get_blacklist_key(str(identify)))

    async def get_menu(self, identify: int | str = None, decode: bool = True):
        menu = await self.get(get_menu_key(None if identify is None else str(identify)))
        if decode and menu:
            menu = json.loads(menu)
        return menu

    async def set_menu(self, identify: int | str = None, value: str = '', encode: bool = True):
        if encode:
            value = json.dumps(value)

        return await self.set(get_menu_key(None if identify is None else str(identify)), value, expire=7 * 24 * 3600)


# TODO 目前只有redis，后续可以扩展
cache = CacheSystem(get_redis())
