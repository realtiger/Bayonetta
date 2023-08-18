from apps.admin.models import Permission
from apps.admin.views.permission_handler.permission_type import PermissionQueryData, PermissionCreateData, PermissionUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter


class PermissionCRUDRouter(SQLAlchemyCRUDRouter):
    pass


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
