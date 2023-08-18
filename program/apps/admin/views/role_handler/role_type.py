from pydantic import Field, BaseModel

from oracle.types import QueryBaseModel, UpdateAddFields


# ### 数据格式定义 ###
# 单个新建格式
class RoleCreateData(BaseModel):
    name: str = Field(default="", description="角色名字", title="角色名字", example="name", min_length=1)
    detail: str = Field(default="", description="详情", title="详情", example="详情信息")


# 单个更新格式
class RoleUpdateData(RoleCreateData, UpdateAddFields):
    pass


#  查询数据返回格式
class RoleQueryData(QueryBaseModel, RoleCreateData):
    pass
