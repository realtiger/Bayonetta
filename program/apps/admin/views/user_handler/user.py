from apps.admin.models import User
from apps.admin.views.user_handler.user_type import UserQueryData, UserCreateData, UserUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter, ValidationError


class UserCRUDRouter(SQLAlchemyCRUDRouter):
    def _create_validator(self, item: dict) -> dict:
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
            return item

        raise ValidationError(f"密码不符合要求: {reason}")


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
