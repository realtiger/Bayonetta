from pydantic import Field, BaseModel

from oracle.types import QueryBaseModel, ModelStatus


# ### 数据格式定义 ###
# 单个新建格式
class RoleCreateData(BaseModel):
    name: str = Field(default="", description="角色名字", title="角色名字", example="name", min_length=1)
    detail: str = Field(default="", description="详情", title="详情", example="详情信息")


# 单个更新格式
class RoleUpdateData(RoleCreateData):
    level: int = Field(default=1, description="排序等级", title="排序等级", example=1, gt=0)
    status: str = Field(default=ModelStatus.ACTIVE, description="数据状态", title="数据状态", example=ModelStatus.ACTIVE)


#  查询数据返回格式
class RoleQueryData(QueryBaseModel, RoleCreateData):
    pass
