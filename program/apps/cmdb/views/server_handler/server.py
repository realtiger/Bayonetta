from apps.cmdb.models import Server, ServerType, CreatedBy
from apps.cmdb.views.server_handler.server_type import ServerQueryData, ServerCreateData, ServerUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter, ValidationError


class ServerCRUDRouter(SQLAlchemyCRUDRouter):
    async def _create_validator(self, item: dict) -> dict:
        server_type = item.get("server_type")
        if server_type not in ServerType.__members__:
            raise ValidationError(f"服务器类型不符合要求: {server_type}")
        created_by = item.get("created_by")
        if created_by not in CreatedBy.__members__:
            raise ValidationError(f"添加方式不符合要求: {created_by}")

        return await super()._create_validator(item)


router = ServerCRUDRouter(
    ServerQueryData,
    Server,
    ServerCreateData,
    ServerUpdateData,
    tags=['server'],
    verbose_name='server',
    # TODO 限制管理员登陆
    get_all_route=True
)
tags_metadata = [{"name": "server", "description": "主机相关接口"}]
