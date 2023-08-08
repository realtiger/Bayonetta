import json

from watchtower import PayloadData
from watchtower.depends.cache.cache import cache as cache_client
from watchtower.settings import logger


async def is_superuser(payload: PayloadData | None) -> bool:
    # TODO 权限判断，这里只是简单的判断是否有管理员字段
    # 现有阶段只判断"status:all"是否存在，后续可根据需求扩展
    # 生成token时，如果是超级用户，会主动将"status:all"加入scopes中
    # 如果是普通用户，只能查看status为active的数据
    if payload is None:
        return False

    is_superuser_value = await cache_client.get_permission(payload.data.id, 'superuser')
    if not is_superuser_value:
        return False

    try:
        is_superuser_value = json.loads(is_superuser_value)
        is_superuser_value = is_superuser_value[0]
        if isinstance(is_superuser_value, bool):
            return is_superuser_value
        else:
            raise ValueError
    except Exception as e:
        logger.error(f'is_superuser_value error: {e}')
        return False
