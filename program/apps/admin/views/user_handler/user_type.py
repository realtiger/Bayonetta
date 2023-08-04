from datetime import datetime

from pydantic import Field, BaseModel

from oracle.types import QueryBaseModel, ModelStatus


# ### 数据格式定义 ###
# 基本新建更新格式
class BaseUserCreateAndUpdateData(BaseModel):
    username: str = Field(default=None, description="用户名", title="用户名", example="username", min_length=1)
    name: str = Field(default=None, description="名字", title="名字", example="name", min_length=1)
    email: str = Field(default=None, description="邮箱", title="邮箱", example="abc@abc.com")
    avatar: str = Field(default=None, description="头像", title="头像", example="/assets/images/avatar/default.jpg")
    detail: str = Field(default=None, description="详情", title="详情", example="详情信息")


# 重置密码
class UserResetPasswordData(BaseModel):
    password: str = Field(default="", description="密码", title="密码", example="password", min_length=8)
    re_password: str = Field(default="", description="确认密码", title="确认密码", example="password")


# 单个更新格式
class UserUpdateData(BaseUserCreateAndUpdateData):
    superuser: bool = Field(default=None, description="是否是超级管理员", title="是否是超级管理员", example=False)
    level: int = Field(default=1, description="排序等级", title="排序等级", example=1, gt=0)
    status: str = Field(default=ModelStatus.ACTIVE, description="数据状态", title="数据状态", example=ModelStatus.ACTIVE)


# 单个新建格式
class UserCreateData(BaseUserCreateAndUpdateData, UserResetPasswordData):
    pass


#  查询数据返回格式
class UserQueryData(UserUpdateData, QueryBaseModel, BaseUserCreateAndUpdateData):
    last_login_ip: str = Field(default="0.0.0.0", description="上次登录ip", title="上次登录ip", example="0.0.0.0")
    last_login_time: datetime = Field(default=datetime.now(), description="上次登录时间", title="上次登录时间", example="2022-11-17T11:23:22.084108")
    roles: list = Field(default=[], description="角色列表，逗号分隔的角色索引", title="角色列表", example=[1, 2, 3])
