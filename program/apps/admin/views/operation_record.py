from pydantic import Field, BaseModel

from apps.admin.models import OperationRecord
from oracle.sqlalchemy import SQLAlchemyCRUDRouter
from oracle.types import QueryBaseModel, ModelStatus
from watchtower.status.types.response import GetAllData


# ### 数据格式定义 ###
# 单个新建格式
class OperationCreateData(BaseModel):
    user_id: int = Field(default=1, description="角色id", title="角色id", example=1)
    data: str = Field(default="", description="详情", title="详情", example="详情信息")


# 单个更新格式
class OperationUpdateData(OperationCreateData):
    level: int = Field(default=1, description="排序等级", title="排序等级", example=1, gt=0)
    status: ModelStatus = Field(default=ModelStatus.ACTIVE, description="数据状态", title="数据状态", example=ModelStatus.ACTIVE)


#  查询数据返回格式
class OperationQueryData(QueryBaseModel, OperationCreateData):
    pass


# 所有数据返回格式
class AllOperationData(GetAllData):
    pass


router = SQLAlchemyCRUDRouter(
    OperationQueryData,
    OperationRecord,
    OperationCreateData,
    OperationUpdateData,
    tags=['operation'],
    get_all_route=True
)
tags_metadata = [{"name": "operation", "description": "角色处理", }]
