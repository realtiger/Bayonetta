from pydantic import Field, BaseModel

from oracle.types import QueryBaseModel, UpdateAddFields


# ### 数据格式定义 ###
class BaseServerAdminCreateAndUpdateData(BaseModel):
    name: str = Field(default="", description="名称", title="名称", example="名称", min_length=1)
    ip: str = Field(default="", description="ip", title="ip", example="ip", min_length=1)
    username: str = Field(default="", description="用户名", title="用户名", example="用户名", min_length=1)
    detail: str = Field(default="", description="备注", title="备注", example="备注信息")


# 单个新建格式
class ServerAdminCreateData(BaseServerAdminCreateAndUpdateData):
    password: str = Field(default="", description="密码", title="密码", example="密码", min_length=1)


# 单个更新格式
class ServerAdminUpdateData(ServerAdminCreateData, UpdateAddFields):
    pass


#  查询数据返回格式
class ServerAdminQueryData(QueryBaseModel, BaseServerAdminCreateAndUpdateData):
    pass


class ServerAdminOperationData(BaseModel):
    operation: str = Field(default="", description="操作", title="操作", example="操作", min_length=1)


class ServerAdminInfoOperationResponseData(ServerAdminOperationData):
    output: str = Field(default="", description="输出", title="输出", example="输出", min_length=1)
    code: int = Field(default=0, description="返回码", title="返回码", example=0)
