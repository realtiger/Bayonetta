from pydantic import Field, BaseModel

from apps.cmdb.models import ServerType, CreatedBy
from apps.cmdb.views.server_handler.server_admin_type import ServerAdminQueryData
from oracle.types import QueryBaseModel, UpdateAddFields


# ### 数据格式定义 ###
# 单个新建格式
class ServerCreateData(BaseModel):
    name: str = Field(default="", description="显示名称", title="显示名称", example="name", min_length=1)
    hostname: str = Field(default="", description="主机名称", title="主机名称", example="hostname", min_length=1)
    server_type: str = Field(default="", description="服务器类型 Rack:机架式 Blade:刀片式 Tower:塔式 PC:PC Mini:迷你", title="服务器类型", example=ServerType.Rack)
    created_by: str = Field(default="", description="添加方式 Manual:手动 Auto:自动", title="添加方式", example=CreatedBy.Manual)
    manager_ip: str = Field(default="", description="管理ip", title="管理ip", example="10.10.10.10")
    private_ip: str = Field(default="", description="内网ip", title="内网ip", example="10.10.10.10")
    public_ip: str = Field(default="", description="公网ip", title="公网ip", example="6.6.6.6")
    port: int = Field(default="", description="登录端口", title="登录端口", example=22)
    idc: str = Field(default="", description="idc", title="idc", example="aws")
    region: str = Field(default="", description="区域", title="区域", example="ap-northeast-1")
    detail: str = Field(default="", description="备注", title="备注", example="备注信息")


# 单个更新格式
class ServerUpdateData(ServerCreateData, UpdateAddFields):
    pass


#  查询数据返回格式
class ServerQueryData(QueryBaseModel, ServerCreateData):
    server_tags: list = Field(default=[], description="标签列表，逗号分隔的标签索引", title="标签列表", example=[1, 2, 3])
    server_admin_info: ServerAdminQueryData = Field(default=None, description="带外管理信息索引", title="带外管理信息索引")
