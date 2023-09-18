from fastapi import Request

from apps.admin.models import OperationRecord
from oracle.sqlalchemy import sql_helper
from watchtower import PayloadData


# TODO 直接存储临时方案
async def save_operation_record(request: Request, app: str, module: str, payload: PayloadData, message: str):
    # TODO 未验证转发情况的客户端ip
    login_ip = request.client.host

    # TODO 集中服务修改，之后需要改成不再依赖固定 model
    async with sql_helper.get_session().begin() as session:
        record = OperationRecord(
            user_id=payload.data.id,
            username=payload.data.username,
            name=payload.data.name,
            login_ip=login_ip,
            method=request.method,
            uri=request.url.path,
            app=app,
            module=module,
            data=message
        )
        session.add(record)

        await session.commit()
        await session.flush()
