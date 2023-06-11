from dataclasses import dataclass
from typing import TypeVar, Generic, Optional, Any

from pydantic import Field, create_model, BaseModel
from pydantic.generics import GenericModel


# 定义状态类型
@dataclass
class Status:
    code: str = 'E99999'
    message: str = '服务器内部错误，请联系管理员'
    success: bool = False


success_status = Status(code='S00000', success=True, message='success')
common_error_status = Status()

DataType = TypeVar("DataType")


class GenericBaseResponse(GenericModel, Generic[DataType]):
    code: str = Field(
        default=success_status.code,
        example=success_status.code,
    )
    success: bool = Field(
        default=success_status.success,
        example=success_status.success,
    )
    message: str = Field(
        default=success_status.message,
        example=success_status.message,
    )
    data: Optional[DataType]

    def __init__(self, status: Status = None, data: dict | BaseModel = None, **kwargs: Any):
        super().__init__(**kwargs)
        if status or data:
            self.update(status, data)

    def update(self, status: Status = None, data: dict | BaseModel = None):
        """
        更新状态信息和数据信息
        :param status: 状态信息
        :param data: 数据信息
        :return:
        """
        if status:
            if self.code != status.code:
                self.code = status.code
            if self.success != status.success:
                self.success = status.success
            if self.message != status.message:
                self.message = status.message
        if data is not None:
            self.data = data

    def as_dict(self):
        if not self.data:
            data = {}
        elif isinstance(self.data, BaseModel):
            data = self.data.dict()
        elif isinstance(self.data, dict):
            data = self.data
        else:
            data = self.data.__dict__

        return {"code": self.code, "success": self.success, "message": self.message, "data": data}


def generate_response_model(model_name: str, status: Status, data: Field = Field(default={})) -> BaseModel:
    """
    生成响应模型
    :param model_name: 模型名称
    :param status: 状态类型
    :param data: 数据类型
    :return:
    """
    code = Field(default=status.code, example=status.code)
    success = Field(default=status.success, example=status.success)
    message = Field(default=status.message, example=status.message)

    return create_model(model_name, code=code, success=success, message=message, data=data)


# ### response 数据格式定义 ###
class PaginationData(BaseModel):
    index: int = Field(default=1, description='查看第几页', title='当前页码', example=1)
    limit: int = Field(default=1, description='每页显示几个数据', title='每页数据', example=20)
    offset: int = Field(default=0, description='从第几个数据开始读取，也就是index和limit的乘积', title='偏移量', example=0)
    total: int = Field(default=0, description='数据总量', title='总数', example=300)


class GetAllData(BaseModel):
    items: list = Field(default=[], description="列表数据", title="数据", example=[])
    pagination: PaginationData
