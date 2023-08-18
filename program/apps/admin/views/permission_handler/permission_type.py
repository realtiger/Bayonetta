from pydantic import Field, BaseModel

from apps.admin.models import PermissionMethods
from oracle.types import QueryBaseModel, UpdateAddFields


# ### 数据格式定义 ###
# 单个新建格式
class PermissionCreateData(BaseModel):
    title: str = Field(default="", description="权限名称", title="权限名称", example="title", min_length=1)
    url: str = Field(default="", description="权限url", title="权限url", example="/")
    method: PermissionMethods = Field(default=PermissionMethods.GET, description="权限请求方法", title="权限请求方法", example=PermissionMethods.GET)
    is_external: bool = Field(default=False, description="是否外部链接", title="是否外部链接", example=False)


# 单个更新格式
class PermissionUpdateData(PermissionCreateData, UpdateAddFields):
    pass


#  查询数据返回格式
class PermissionQueryData(QueryBaseModel, PermissionCreateData):
    code: str = Field(default="", description="权限代码", title="权限代码", example="system:get-all-permission")

