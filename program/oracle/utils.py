from sqlalchemy import select

from watchtower import PayloadData
from watchtower.depends.cache.cache import cache as cache_client


async def is_superuser(payload: PayloadData | None) -> bool:
    # TODO 权限判断，这里只是简单的判断是否有管理员字段
    # 现有阶段只判断"status:all"是否存在，后续可根据需求扩展
    # 生成token时，如果是超级用户，会主动将"status:all"加入scopes中
    # 如果是普通用户，只能查看status为active的数据
    if payload is None or not payload.data:
        return False

    is_superuser_value = await cache_client.get_permission(payload.data.id, 'superuser')
    is_superuser_value = is_superuser_value[0] if isinstance(is_superuser_value, list) else False
    if isinstance(is_superuser_value, bool):
        return is_superuser_value
    else:
        return False


def extend_tags_metadata(source: list = None, *args):
    tags_metadata = source or []
    for arg in args:
        tags_metadata.extend(arg)
    return tags_metadata


# TODO 临时解决方案，后续需要优化
async def merge_m2m_field(session, m2m_row, m2m_model, update_ids):
    m2m_row_ids = {item.id for item in m2m_row}
    add_m2m_row_ids = set(update_ids) - m2m_row_ids
    remove_m2m_row_ids = m2m_row_ids - set(update_ids)

    if add_m2m_row_ids:
        add_m2m_row_statement = select(m2m_model).where(m2m_model.id.in_(add_m2m_row_ids))
        add_m2m_rows = await session.execute(add_m2m_row_statement)
        for add_m2m_row in add_m2m_rows.scalars().all():
            m2m_row.append(add_m2m_row)
    if remove_m2m_row_ids:
        remove_m2m_row_statement = select(m2m_model).where(m2m_model.id.in_(remove_m2m_row_ids))
        remove_m2m_rows = await session.execute(remove_m2m_row_statement)
        for remove_m2m_row in remove_m2m_rows.scalars().all():
            m2m_row.remove(remove_m2m_row)
    await session.commit()
    await session.flush()
