from sqlalchemy import Select

from apps.cmdb.models import ServerTag
from oracle.sqlalchemy import sql_helper


async def run(*args, **kwargs):
    session_maker = sql_helper.get_session()

    async with session_maker.begin() as session:
        # 确保有一个默认的标签
        select_default_server_tag_statement = Select(ServerTag).where(ServerTag.id == 1)
        default_server_tag = (await session.execute(select_default_server_tag_statement)).scalar_one_or_none()

        if not default_server_tag:
            default_server_tag = ServerTag(name="default", detail="默认标签")
            session.add(default_server_tag)

        await session.commit()
        await session.flush()
