from pydantic import Field, BaseModel

from oracle.sqlalchemy import ITEM_NOT_FOUND_RESPONSE
from watchtower import generate_response_model
from watchtower.status.global_status import StatusMap

GET_KUBE_RESOURCE_FAILED_CODE = 280

GET_KUBE_RESOURCE_ERROR_RESPONSE = {
    GET_KUBE_RESOURCE_FAILED_CODE: {
        "model": generate_response_model('GET_KUBE_RESOURCE_FAILED', StatusMap.KUBE_GET_RESOURCE_FAILED),
        "description": "获取k8s资源失败",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.KUBE_GET_RESOURCE_FAILED.code,
                    "success": StatusMap.KUBE_GET_RESOURCE_FAILED.success,
                    "message": StatusMap.KUBE_GET_RESOURCE_FAILED.message,
                    "data": {}
                }
            }
        }
    }
}

GET_KUBE_RESOURCE_ERROR_RESPONSE.update(ITEM_NOT_FOUND_RESPONSE)


# ##### PODS #####
class PodData(BaseModel):
    id: str = Field(description="pod uid", title="pod uid", example="uid")
    name: str = Field(description="pod名字", title="pod名字", example="name")
    status: str = Field(description="pod状态", title="pod状态", example="Active")


#  查询数据返回格式
class KubeOperationQueryPodsData(BaseModel):
    items: list[PodData] = Field(default=[], description="pod列表", title="pod列表", example=[{"name": "name"}])


# ##### NAMESPACE #####
class NamespaceData(BaseModel):
    id: str = Field(description="namespace uid", title="namespace uid", example="uid")
    name: str = Field(description="namespace名字", title="namespace名字", example="name")
    status: str = Field(description="namespace状态", title="namespace状态", example="Active")


#  查询数据返回格式
class KubeOperationQueryNamespacesData(BaseModel):
    items: list[NamespaceData] = Field(default=[], description="namespace列表", title="namespace列表", example=[{"name": "name"}])


# ##### DEPLOYMENT #####
class DeploymentStatusData(BaseModel):
    replicas: int = Field(description="deployment副本数", title="deployment副本数", example=1)
    available: int = Field(description="deployment可用副本数", title="deployment可用副本数", example=1)
    unavailable: int = Field(description="deployment不可用副本数", title="deployment不可用副本数", example=1)
    ready: int = Field(description="deployment就绪副本数", title="deployment就绪副本数", example=1)
    updated: int = Field(description="deployment更新副本数", title="deployment更新副本数", example=1)


class DeploymentData(BaseModel):
    id: str = Field(description="deployment uid", title="deployment uid", example="uid")
    name: str = Field(description="deployment名字", title="deployment名字", example="name")
    status: DeploymentStatusData = Field(description="deployment状态", title="deployment状态", example={"replicas": 1})


#  查询数据返回格式
class KubeOperationQueryDeploymentsData(BaseModel):
    items: list[DeploymentData] = Field(default=[], description="deployment列表", title="deployment列表", example=[{"name": "name"}])
