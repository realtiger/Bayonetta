from apps.admin.models import Role
from apps.admin.views.role_handler.role_type import RoleQueryData, RoleCreateData, RoleUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter


class RoleCRUDRouter(SQLAlchemyCRUDRouter):
    pass


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
