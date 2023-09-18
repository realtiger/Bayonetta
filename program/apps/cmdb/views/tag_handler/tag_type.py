from pydantic import Field, BaseModel

from oracle.types import QueryBaseModel, UpdateAddFields


# ### 数据格式定义 ###
# 单个新建格式
class ServerTagCreateData(BaseModel):
    name: str = Field(description="标签名称", title="标签名称", example="标签名称", min_length=1)
    detail: str = Field(default="", description="备注", title="备注", example="备注信息")


# 单个更新格式
class ServerTagUpdateData(ServerTagCreateData, UpdateAddFields):
    pass


#  查询数据返回格式
class ServerTagQueryData(QueryBaseModel, ServerTagCreateData):
    pass
