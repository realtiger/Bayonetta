from sqlalchemy import Update, Select

from apps.admin.models import Permission
from apps.admin.views.permission_handler.permission_type import PermissionQueryData, PermissionCreateData, PermissionUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter
from oracle.types import ModelStatus, PAGINATION
from oracle.utils import is_superuser
from watchtower import PayloadData


class PermissionCRUDRouter(SQLAlchemyCRUDRouter):
    async def _orm_get_one_statement(self, filters: dict[str, str | list], payload: PayloadData | None) -> Select:
        # 普通用户只能查看 active 状态的数据
        status_list = [ModelStatus.ACTIVE.value]
        # 超级用户可以查看所有状态的数据
        if await is_superuser(payload):
            status_list.extend([ModelStatus.INACTIVE.value, ModelStatus.FROZEN.value])

        filters['status'] = status_list

        return await super()._orm_get_one_statement(filters, payload)

    async def _orm_get_all_statement(
            self,
            pagination: PAGINATION,
            filters: dict[str, str | list],
            orders: list,
            ids: list[int],
            payload: PayloadData | None
    ) -> tuple[Select, Select]:
        # 普通用户只能查看 active 状态的数据
        status_list = [ModelStatus.ACTIVE.value]
        # 超级用户可以查看所有状态的数据
        if await is_superuser(payload):
            status_list.extend([ModelStatus.INACTIVE.value, ModelStatus.FROZEN.value])

        filters['status'] = status_list

        return await super()._orm_get_all_statement(pagination, filters, orders, ids, payload)

    async def _orm_update_statement(self, item_id: int, data: dict, payload: PayloadData | None = None) -> Update:
        # 非超级管理员用户无法修改状态
        if "status" in data:
            data.pop("status")

        return await super()._orm_update_statement(item_id, data, payload)


router = PermissionCRUDRouter(
    PermissionQueryData,
    Permission,
    PermissionCreateData,
    PermissionUpdateData,
    tags=['permission'],
    verbose_name='permission',
    create_route=False,
    update_route=False,
    delete_one_route=False,
)
tags_metadata = [{"name": "permission", "description": "权限相关接口"}]
