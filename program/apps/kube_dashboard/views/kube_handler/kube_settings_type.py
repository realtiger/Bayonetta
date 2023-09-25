from pydantic import Field, BaseModel

from oracle.types import QueryBaseModel, UpdateAddFields


# ### 数据格式定义 ###
# 基本新建更新格式
class BaseKubeSettingsCreateAndUpdateData(BaseModel):
    name: str = Field(description="名字", title="名字", example="name", min_length=1)
    conf: str = Field(description="配置内容", title="配置内容", example="conf", min_length=1)
    description: str = Field(default='', description="描述", title="描述", example="description")


# 单个更新格式
class KubeSettingsUpdateData(BaseKubeSettingsCreateAndUpdateData, UpdateAddFields):
    pass


# 单个新建格式
class KubeSettingsCreateData(BaseKubeSettingsCreateAndUpdateData):
    pass


#  查询数据返回格式
class KubeSettingsQueryData(KubeSettingsUpdateData, QueryBaseModel, BaseKubeSettingsCreateAndUpdateData):
    pass
