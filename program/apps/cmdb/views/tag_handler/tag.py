from fastapi import Request

from apps.admin.models import OperationRecord
from apps.cmdb.models import ServerTag
from apps.cmdb.views.tag_handler.tag_type import ServerTagQueryData, ServerTagCreateData, ServerTagUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter
from watchtower import PayloadData
from watchtower.settings import logger


class ServerTagCRUDRouter(SQLAlchemyCRUDRouter):
    app = 'cmdb'
    module = 'server_tag'

    async def _post_create(self, item, request: Request | None = None, payload: PayloadData | None = None):
        # TODO 未验证转发情况的客户端ip
        login_ip = request.client.host

        # TODO 集中服务修改，之后需要改成不再依赖固定 model
        # 记录新建主机标签，并且记录时出错不影响用户正常添加
        try:
            async with self.db_func().begin() as session:
                record_for_create_server = OperationRecord(
                    user_id=payload.data.id,
                    username=payload.data.username,
                    name=payload.data.name,
                    login_ip=login_ip,
                    method=request.method,
                    uri=request.url.path,
                    app=self.app,
                    module=self.module,
                    data=f"新建主机标签: {item}"
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
                    app=self.app,
                    module=self.module,
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
                    app=self.app,
                    module=self.module,
                    data=data
                )
                session.add(record_for_delete_server)

                await session.commit()
                await session.flush()
        except Exception as error:
            logger.error(f"记录删除主机记录时出错: {error}")

        return item


router = ServerTagCRUDRouter(
    ServerTagQueryData,
    ServerTag,
    ServerTagCreateData,
    ServerTagUpdateData,
    tags=['server-tag'],
    verbose_name='server_tag',
    delete_all_route=True
)
tags_metadata = [{"name": "server-tag", "description": "主机标签相关接口"}]
