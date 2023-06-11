from datetime import datetime
from enum import Enum
from typing import TypeVar, Sequence

from fastapi import Depends
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)
DEPENDENCIES = Sequence[Depends] | None
PYDANTIC_SCHEMA = BaseModel


class PAGINATION(BaseModel):
    index: int = 1
    limit: int = 10
    offset: int = 0
    max_limit: int = 10
    total: int = 0


class ModelStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FROZEN = "frozen"
    OBSOLETE = "obsolete"


# 默认的查询模型需要包含的字段
class QueryBaseModel(BaseModel):
    id: int = Field(default=0, description="数据索引", title="数据索引", example=1)
    level: int = Field(default=1, description="排序等级", title="排序等级", example=1)
    status: ModelStatus = Field(default=ModelStatus.ACTIVE, description="数据状态", title="数据状态", example=ModelStatus.ACTIVE)
    create_time: datetime = Field(default=datetime.now(), description="创建时间", title="创建时间", example="2022-11-17T11:23:22.084108")
    update_time: datetime = Field(default=datetime.now(), description="修改时间", title="修改时间", example="2022-11-17T11:23:22.084108")


class DeleteData(BaseModel):
    count: int = Field(default=0, description="删除的数据量", title="数据量", example=10)
    identifiers: list = Field(default=[], description="删除的数据索引", title="数据索引", example=[1, 2, 3])
