from pydantic import Field

from apps.admin.models import PermissionMethods
from oracle.types import QueryBaseModel


# ### 数据格式定义 ###
# 查询数据返回格式
class OperationQueryData(QueryBaseModel):
    user_id: int = Field(default=0, description="用户id", title="用户id", example=1)
    username: str = Field(default="", description="用户名", title="用户名", example="admin")
    name: str = Field(default="", description="用户展示名称", title="用户展示名称", example="管理员")
    login_ip: str = Field(default="", description="登录ip", title="登录ip", example="10.10.10.10")
    method: PermissionMethods = Field(default=PermissionMethods.GET, description="请求方法", title="请求方法", example=PermissionMethods.GET)
    uri: str = Field(default="", description="请求uri", title="请求uri", example="/api/v1/user")
    data: str = Field(default="", description="请求数据", title="请求数据", example="请求数据详情信息")
