from datetime import datetime
from enum import Enum
from typing import TypeVar, Sequence

from fastapi import Depends
from pydantic import BaseModel, Field

# 定义规定的错误码
ITEM_NOT_FOUND_CODE = 264
MULTIPLE_RESULTS_FOUND_CODE = 265
PRIMARY_KEY_EXISTED_CODE = 266
CREATE_FAILED_CODE = 267
UPDATE_FAILED_CODE = 268
DELETE_FAILED_CODE = 269
ONLY_SUPERUSER_CODE = 270

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


class UpdateAddFields(BaseModel):
    level: int = Field(default=1, description="排序等级", title="排序等级", example=1, gt=0)
    status: str = Field(default=ModelStatus.ACTIVE, description="数据状态", title="数据状态", example=ModelStatus.ACTIVE)


class DeleteData(BaseModel):
    count: int = Field(default=0, description="删除的数据量", title="数据量", example=10)
    identifiers: list = Field(default=[], description="删除的数据索引", title="数据索引", example=[1, 2, 3])
