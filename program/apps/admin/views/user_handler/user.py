from fastapi import Depends, Body
from sqlalchemy import Update, select, Select
from sqlalchemy.orm import selectinload

from apps.admin.models import User, Role
from apps.admin.views.user_handler.user_type import UserQueryData, UserCreateData, UserUpdateData, UserResetPasswordData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter, ValidationError, ITEM_NOT_FOUND_RESPONSE, ONLY_SUPERUSER_RESPONSE
from oracle.types import ITEM_NOT_FOUND_CODE, ONLY_SUPERUSER_CODE, CREATE_FAILED_CODE, DELETE_FAILED_CODE, ModelStatus, PAGINATION
from oracle.utils import is_superuser
from watchtower import PayloadData, SiteException
from watchtower.depends.authorization.authorization import get_password_hash, signature_authentication
from watchtower.status.global_status import StatusMap
from watchtower.status.types.response import GenericBaseResponse, Status, generate_response_model

CURRENT_USER_NOT_PERMISSION_CODE = 271
PasswordValidationFailed = generate_response_model("PasswordValidationFailed", StatusMap.DATA_VALIDATION_FAILED)
CurrentUserNotPermission = generate_response_model("CurrentUserNotPermission", StatusMap.CURRENT_USER_NOT_PERMISSION)

update_user_roles_responses = ITEM_NOT_FOUND_RESPONSE | ONLY_SUPERUSER_RESPONSE

password_valid_failed_responses = {
    CREATE_FAILED_CODE: {
        "model": PasswordValidationFailed,
        "description": "密码不符合要求",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.DATA_VALIDATION_FAILED.code,
                    "success": StatusMap.DATA_VALIDATION_FAILED.success,
                    "message": StatusMap.DATA_VALIDATION_FAILED.message,
                    "data": {}
                }
            }
        }
    },
    CURRENT_USER_NOT_PERMISSION_CODE: {
        "model": CurrentUserNotPermission,
        "description": "当前用户权限不足",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.CURRENT_USER_NOT_PERMISSION.code,
                    "success": StatusMap.CURRENT_USER_NOT_PERMISSION.success,
                    "message": StatusMap.CURRENT_USER_NOT_PERMISSION.message,
                    "data": {}
                }
            }
        }
    }
}
password_valid_failed_responses.update(ITEM_NOT_FOUND_RESPONSE)


def check_password(password: str, re_password: str):
    if not password:
        reason = "密码不能为空"
    elif not re_password:
        reason = "确认密码不能为空"
    elif password != re_password:
        reason = "两次密码不一致"
    elif len(password) < 8:
        reason = "密码长度不能小于8位"
    else:
        return True, None

    return False, reason


class UserCRUDRouter(SQLAlchemyCRUDRouter):
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

    async def _create_validator(self, item: dict) -> dict:
        password = item.get("password")
        re_password = item.get("re_password")
        valid, reason = check_password(password, re_password)
        if valid:
            item["password"] = await get_password_hash(password.encode())
            return item

        raise ValidationError(f"密码不符合要求: {reason}")

    async def _orm_update_statement(self, item_id: int, data: dict, payload: PayloadData | None = None) -> Update:
        if not await is_superuser(payload):
            # 想要给item设置superuser但是当前用户不是superuser，则直接取消superuser的设置
            if 'superuser' in data:
                data.pop('superuser')

            # 非超级管理员用户无法修改自己的状态
            if "status" in data:
                data.pop("status")

        return await super()._orm_update_statement(item_id, data, payload)

    async def _pre_delete(self, data: dict):
        if data.get('superuser'):
            status = Status(StatusMap.DELETE_FAILED.code, "超级管理员用户无法被删除")
            raise SiteException(status_code=DELETE_FAILED_CODE, response=GenericBaseResponse[dict](status=status)) from None
        return data


router = UserCRUDRouter(
    UserQueryData,
    User,
    UserCreateData,
    UserUpdateData,
    tags=['user'],
    verbose_name='User',
    # TODO 限制管理员登陆
    get_all_route=True
)
tags_metadata = [{"name": "user", "description": "用户处理"}]


@router.put("/{user_id}/roles", summary="修改用户角色", description="修改用户角色", response_model=UserQueryData, responses=update_user_roles_responses)
async def update_user_roles(user_id: int, roles: list[int] = Body(default=None, embed=True), payload: PayloadData = Depends(signature_authentication)):
    """
    修改用户角色
    \f
    :param user_id:
    :param roles:
    :param payload:
    :return:
    """
    user_statement = select(User).join(User.roles, isouter=True).options(selectinload(User.roles)).where(User.id == user_id).distinct()
    async with router.db_func().begin() as session:
        user = await session.execute(user_statement)
        user = user.scalar_one_or_none()
        if not user:
            status = Status(code=StatusMap.ITEM_NOT_FOUND.code, message="没有找到用户")
            response = GenericBaseResponse[dict](status=status)
            raise SiteException(status_code=ITEM_NOT_FOUND_CODE, response=response) from None

        if not await is_superuser(payload):
            status = Status(code=StatusMap.ONLY_SUPERUSER.code, message="当前用户不是超级管理员，无法修改用户角色")
            response = GenericBaseResponse[dict](status=status)
            raise SiteException(status_code=ONLY_SUPERUSER_CODE, response=response) from None
        user_role_ids = {role.id for role in user.roles}
        add_roles_ids = set(roles) - user_role_ids
        remove_roles_ids = user_role_ids - set(roles)

        if add_roles_ids:
            add_roles_statement = select(Role).where(Role.id.in_(add_roles_ids))
            add_roles = await session.execute(add_roles_statement)
            user.roles.extend(add_roles.scalars().all())
        if remove_roles_ids:
            remove_roles_statement = select(Role).where(Role.id.in_(remove_roles_ids))
            remove_roles = await session.execute(remove_roles_statement)
            for role in remove_roles.scalars().all():
                user.roles.remove(role)
        await session.commit()
        await session.flush()

    data = router.format_query_data(user)
    return GenericBaseResponse[UserQueryData](data=data)


@router.put("/{user_id}/reset_password", summary="重置用户密码", description="重置用户密码", response_model=UserQueryData, responses=password_valid_failed_responses)
async def reset_password(user_id: int, password: UserResetPasswordData, payload: PayloadData = Depends(signature_authentication)):
    valid, reason = check_password(password.password, password.re_password)
    if not valid:
        status = Status(code=StatusMap.DATA_VALIDATION_FAILED.code, message=reason)
        response = GenericBaseResponse[dict](status=status)
        raise SiteException(status_code=CREATE_FAILED_CODE, response=response) from None

    # 如果当前用户不是超级管理员也不是自己进行密码重置操作，则无法进行密码重置
    if not await is_superuser(payload) and user_id != payload.data.id:
        status = Status(code=StatusMap.CURRENT_USER_NOT_PERMISSION.code, message="当前用户权限不足")
        response = GenericBaseResponse[dict](status=status)
        raise SiteException(status_code=CURRENT_USER_NOT_PERMISSION_CODE, response=response) from None

    async with router.db_func().begin() as session:
        user_statement = select(User).join(User.roles, isouter=True).options(selectinload(User.roles)).where(User.id == user_id).distinct()
        user = (await session.execute(user_statement)).scalar_one_or_none()
        if not user:
            status = Status(code=StatusMap.ITEM_NOT_FOUND.code, message="没有找到用户")
            response = GenericBaseResponse[dict](status=status)
            raise SiteException(status_code=ITEM_NOT_FOUND_CODE, response=response) from None

        user.password = await get_password_hash(password.password.encode())
        await session.commit()
        await session.flush()

    return GenericBaseResponse[UserQueryData](data=router.format_query_data(user))
