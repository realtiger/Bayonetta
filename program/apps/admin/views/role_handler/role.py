from fastapi import Body, Depends
from sqlalchemy import Update, Select, select
from sqlalchemy.orm import selectinload

from apps.admin.models import Role, Permission
from apps.admin.views.role_handler.role_type import RoleQueryData, RoleCreateData, RoleUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter, ITEM_NOT_FOUND_RESPONSE, ONLY_SUPERUSER_RESPONSE
from oracle.types import ModelStatus, PAGINATION, ITEM_NOT_FOUND_CODE, ONLY_SUPERUSER_CODE
from oracle.utils import is_superuser, merge_m2m_field
from watchtower import PayloadData, SiteException, signature_authentication
from watchtower.status.global_status import StatusMap
from watchtower.status.types.response import Status, GenericBaseResponse

update_role_permissions_responses = ITEM_NOT_FOUND_RESPONSE | ONLY_SUPERUSER_RESPONSE


class RoleCRUDRouter(SQLAlchemyCRUDRouter):
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


router = RoleCRUDRouter(
    RoleQueryData,
    Role,
    RoleCreateData,
    RoleUpdateData,
    tags=['role'],
    verbose_name='role',
    # TODO 限制管理员登陆
    get_all_route=True
)
tags_metadata = [{"name": "role", "description": "角色相关接口"}]


@router.put("/{role_id}/permissions", summary="修改角色权限", description="修改角色权限", response_model=RoleQueryData, responses=update_role_permissions_responses)
async def update_role_permissions(role_id: int, permissions: list[int] = Body(default=None, embed=True), payload: PayloadData = Depends(signature_authentication)):
    """
    修改角色权限
    \f
    :param role_id:
    :param permissions:
    :param payload:
    :return:
    """
    role_statement = select(Role).join(Role.permissions, isouter=True).options(selectinload(Role.permissions)).where(Role.id == role_id).distinct()
    async with router.db_func().begin() as session:
        role = await session.execute(role_statement)
        role = role.scalar_one_or_none()
        if not role:
            status = Status(code=StatusMap.ITEM_NOT_FOUND.code, message="没有找到角色")
            raise SiteException(status_code=ITEM_NOT_FOUND_CODE, response=GenericBaseResponse[dict](status=status)) from None

        if not await is_superuser(payload):
            status = Status(code=StatusMap.ONLY_SUPERUSER.code, message="当前用户不是超级管理员，无法修改角色权限")
            raise SiteException(status_code=ONLY_SUPERUSER_CODE, response=GenericBaseResponse[dict](status=status)) from None

        await merge_m2m_field(session, role.permissions, Permission, permissions)

    data = await router.format_query_data(role)
    return GenericBaseResponse[RoleQueryData](data=data)
