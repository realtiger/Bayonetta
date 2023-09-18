from fastapi import Request, Body, Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.admin.models import OperationRecord
from apps.cmdb.models import Server, ServerType, CreatedBy, ServerTag
from apps.cmdb.views.server_handler.server_type import ServerQueryData, ServerCreateData, ServerUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter, ValidationError, ITEM_NOT_FOUND_RESPONSE
from oracle.types import ITEM_NOT_FOUND_CODE
from oracle.utils import merge_m2m_field
from watchtower import PayloadData, signature_authentication, SiteException
from watchtower.settings import logger
from watchtower.status.global_status import StatusMap
from watchtower.status.types.response import GenericBaseResponse, Status


class ServerCRUDRouter(SQLAlchemyCRUDRouter):
    async def _create_validator(self, item: dict) -> dict:
        server_type = item.get("server_type")
        if server_type not in ServerType.__members__:
            raise ValidationError(f"服务器类型不符合要求: {server_type}")
        created_by = item.get("created_by")
        if created_by not in CreatedBy.__members__:
            raise ValidationError(f"添加方式不符合要求: {created_by}")

        return await super()._create_validator(item)

    async def _post_create(self, item, request: Request | None = None, payload: PayloadData | None = None):
        # TODO 未验证转发情况的客户端ip
        login_ip = request.client.host

        # TODO 集中服务修改，之后需要改成不再依赖固定 model
        # 记录新建主机，并且记录时出错不影响用户正常添加
        try:
            async with self.db_func().begin() as session:
                record_for_create_server = OperationRecord(
                    user_id=payload.data.id,
                    username=payload.data.username,
                    name=payload.data.name,
                    login_ip=login_ip,
                    method=request.method,
                    uri=request.url.path,
                    app='cmdb',
                    module='server',
                    data=f"新建主机记录: {item}"
                )
                session.add(record_for_create_server)

                await session.commit()
                await session.flush()
        except Exception as error:
            logger.error(f"记录新建主机记录时出错: {error}")

    async def _post_update(self, item: dict, original_data: dict, request: Request | None = None, payload: PayloadData | None = None) -> dict:
        # TODO 未验证转发情况的客户端ip
        login_ip = request.client.host

        data = f"更新前数据: {original_data}, 更新后数据: {item}"
        # 记录更新主机，并且记录时出错不影响用户正常更新
        try:
            async with self.db_func().begin() as session:
                record_for_update_server = OperationRecord(
                    user_id=payload.data.id,
                    username=payload.data.username,
                    name=payload.data.name,
                    login_ip=login_ip,
                    method=request.method,
                    uri=request.url.path,
                    app='cmdb',
                    module='server',
                    data=data
                )
                session.add(record_for_update_server)

                await session.commit()
                await session.flush()
        except Exception as error:
            logger.error(f"记录更新主机记录时出错: {error}")

        return item

    async def _post_delete(self, item: dict, request: Request | None = None, payload: PayloadData | None = None) -> dict:
        # TODO 未验证转发情况的客户端ip
        login_ip = request.client.host

        data = f"删除数据: {item}"
        # 记录删除主机，并且记录时出错不影响用户正常删除
        try:
            async with self.db_func().begin() as session:
                record_for_delete_server = OperationRecord(
                    user_id=payload.data.id,
                    username=payload.data.username,
                    name=payload.data.name,
                    login_ip=login_ip,
                    method=request.method,
                    uri=request.url.path,
                    app='cmdb',
                    module='server',
                    data=data
                )
                session.add(record_for_delete_server)

                await session.commit()
                await session.flush()
        except Exception as error:
            logger.error(f"记录删除主机记录时出错: {error}")

        return item


router = ServerCRUDRouter(
    ServerQueryData,
    Server,
    ServerCreateData,
    ServerUpdateData,
    tags=['server'],
    verbose_name='server',
    get_all_route=True
)
tags_metadata = [{"name": "server", "description": "主机相关接口"}]


@router.put("/{server_id}/tags", summary="修改主机标签", description="修改主机标签", response_model=ServerQueryData, responses=ITEM_NOT_FOUND_RESPONSE)
async def update_server_to_server_tag(server_id: int, tags: list[int] = Body(default=None, embed=True), payload: PayloadData = Depends(signature_authentication)):
    """
    修改用户角色
    \f
    :param server_id:
    :param tags:
    :param payload:
    :return:
    """
    server_statement = select(Server).join(Server.server_tags, isouter=True).options(selectinload(Server.server_tags)).where(Server.id == server_id).distinct()
    async with router.db_func().begin() as session:
        server = await session.execute(server_statement)
        server = server.scalar_one_or_none()
        if not server:
            status = Status(code=StatusMap.ITEM_NOT_FOUND.code, message="没有找到服务器")
            response = GenericBaseResponse[dict](status=status)
            raise SiteException(status_code=ITEM_NOT_FOUND_CODE, response=response) from None

        await merge_m2m_field(session, server.server_tags, ServerTag, tags)

    data = await router.format_query_data(server)
    return GenericBaseResponse[ServerQueryData](data=data)
