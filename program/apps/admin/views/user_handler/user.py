from sqlalchemy import Update

from apps.admin.models import User
from apps.admin.views.user_handler.user_type import UserQueryData, UserCreateData, UserUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter, ValidationError
from oracle.utils import is_superuser
from watchtower import PayloadData
from watchtower.depends.authorization.authorization import get_password_hash


class UserCRUDRouter(SQLAlchemyCRUDRouter):
    async def _create_validator(self, item: dict) -> dict:
        password = item.get("password")
        re_password = item.get("re_password")
        if not password:
            reason = "密码不能为空"
        elif not re_password:
            reason = "确认密码不能为空"
        elif password != re_password:
            reason = "两次密码不一致"
        elif len(password) < 8:
            reason = "密码长度不能小于8位"
        else:
            item["password"] = await get_password_hash(password.encode())
            return item

        raise ValidationError(f"密码不符合要求: {reason}")

    async def _orm_update_statement(self, item_id: int, data: dict, payload: PayloadData | None = None) -> Update:
        if not await is_superuser(payload):
            # 想要给item设置superuser但是当前用户不是superuser，则直接取消superuser的设置
            data.pop('superuser')

        return await super()._orm_update_statement(item_id, data, payload)


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
tags_metadata = [{"name": "user", "description": "用户处理", }]
