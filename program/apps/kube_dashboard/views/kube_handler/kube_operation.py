import json

from fastapi import APIRouter, Depends
from httpx import ReadTimeout, ConnectTimeout
from sqlalchemy import Select

from apps.kube_dashboard.models import KubeSettings
from apps.kube_dashboard.views.kube_handler.kube_operation_type import KubeOperationQueryPodsData, GET_KUBE_RESOURCE_ERROR_RESPONSE, GET_KUBE_RESOURCE_FAILED_CODE, \
    KubeOperationQueryNamespacesData, KubeOperationQueryDeploymentsData
from apps.kube_dashboard.views.kube_handler.kube_service import KubeService
from oracle.sqlalchemy import sql_helper
from oracle.types import ITEM_NOT_FOUND_CODE
from watchtower import SiteException
from watchtower.depends.cache.cache import CacheSystem, cache
from watchtower.settings import logger
from watchtower.status.global_status import StatusMap
from watchtower.status.types.response import Status, GenericBaseResponse

router = APIRouter(prefix='/kube-operation', tags=["kube-operation"])
tags_metadata = [{"name": "kube-operation", "description": "k8s操作接口"}]


async def get_kube_service(conf: int, cache_client: CacheSystem) -> KubeService:
    """
    根据settings的id 获取自定义kube服务object 所有的操作都定义在这个对象里面
    :param conf:
    :param cache_client:
    :return:
    """
    select_kube_settings_statement = Select(KubeSettings).where(KubeSettings.id == conf)

    kube_settings = await cache_client.get(f'kube_settings_{conf}')
    if not kube_settings:
        async with sql_helper.get_session().begin() as session:
            kube_settings = await session.execute(select_kube_settings_statement)
            kube_settings = kube_settings.scalar_one_or_none()
            if not kube_settings:
                status = Status(code=StatusMap.ITEM_NOT_FOUND.code, message="没有找到k8s配置信息")
                response = GenericBaseResponse[dict](status=status)
                raise SiteException(status_code=ITEM_NOT_FOUND_CODE, response=response) from None
            kube_settings = {"id": kube_settings.id, "conf": kube_settings.conf, "description": kube_settings.description}
            await cache_client.set(f'kube_settings_{conf}', json.dumps(kube_settings), 30 * 60)
    else:
        kube_settings = json.loads(kube_settings)
    kube_service = KubeService(kube_settings['conf'])

    return kube_service


@router.get('/namespaces', response_model=GenericBaseResponse[list[str]], responses=GET_KUBE_RESOURCE_ERROR_RESPONSE)
async def get_all_namespaces(conf: int, cache_client: CacheSystem = Depends(cache)):
    try:
        kube_service = await get_kube_service(conf, cache_client)
        namespaces = await kube_service.list_namespace()
    except ConnectTimeout:
        logger.error("k8s集群连接超时")
        response = GenericBaseResponse[dict](status=StatusMap.KUBE_GET_RESOURCE_FAILED)
        raise SiteException(status_code=GET_KUBE_RESOURCE_FAILED_CODE, response=response) from None
    except ReadTimeout:
        logger.error("k8s集群读取超时")
        response = GenericBaseResponse[dict](status=StatusMap.KUBE_GET_RESOURCE_FAILED)
        raise SiteException(status_code=GET_KUBE_RESOURCE_FAILED_CODE, response=response) from None
    data = list()
    for namespace in namespaces['items']:
        data.append({
            'name': namespace['metadata']['name'],
            'id': namespace['metadata']['uid'],
            'status': namespace['status']['phase'],
        })

    data = KubeOperationQueryNamespacesData(items=data).dict()
    return GenericBaseResponse[list[KubeOperationQueryNamespacesData]](data=data)


@router.get('/namespaces/{namespace}/deployment', response_model=GenericBaseResponse[KubeOperationQueryDeploymentsData], responses=GET_KUBE_RESOURCE_ERROR_RESPONSE)
async def get_all_pods_by_namespace(namespace: str, conf: int, cache_client: CacheSystem = Depends(cache)):
    try:
        kube_service = await get_kube_service(conf, cache_client)
        deployments = await kube_service.list_namespaced_deployment(namespace)
    except ConnectTimeout:
        logger.error("k8s集群连接超时")
        response = GenericBaseResponse[dict](status=StatusMap.KUBE_GET_RESOURCE_FAILED)
        raise SiteException(status_code=GET_KUBE_RESOURCE_FAILED_CODE, response=response) from None
    except ReadTimeout:
        logger.error("k8s集群读取超时")
        response = GenericBaseResponse[dict](status=StatusMap.KUBE_GET_RESOURCE_FAILED)
        raise SiteException(status_code=GET_KUBE_RESOURCE_FAILED_CODE, response=response) from None
    data = list()
    for deployment in deployments['items']:
        data.append({
            'name': deployment['metadata']['name'],
            'id': deployment['metadata']['uid'],
            'status': {
                'replicas': deployment['spec'].get('replicas', 0),
                'available': deployment['status'].get('availableReplicas', 0),
                'unavailable': deployment['status'].get('unavailableReplicas', 0),
                'ready': deployment['status'].get('readyReplicas', 0),
                'updated': deployment['status'].get('updatedReplicas', 0),
            }
        })

    data = KubeOperationQueryDeploymentsData(items=data).dict()
    return GenericBaseResponse[list[KubeOperationQueryDeploymentsData]](data=data)


@router.get('/pods', response_model=GenericBaseResponse[KubeOperationQueryPodsData], responses=GET_KUBE_RESOURCE_ERROR_RESPONSE)
async def get_all_pods(conf: int, cache_client: CacheSystem = Depends(cache)):
    try:
        kube_service = await get_kube_service(conf, cache_client)
        pods = await kube_service.list_pod_for_all_namespaces()
    except ConnectTimeout:
        logger.error("k8s集群连接超时")
        response = GenericBaseResponse[dict](status=StatusMap.KUBE_GET_RESOURCE_FAILED)
        raise SiteException(status_code=GET_KUBE_RESOURCE_FAILED_CODE, response=response) from None
    except ReadTimeout:
        logger.error("k8s集群读取超时")
        response = GenericBaseResponse[dict](status=StatusMap.KUBE_GET_RESOURCE_FAILED)
        raise SiteException(status_code=GET_KUBE_RESOURCE_FAILED_CODE, response=response) from None
    data = list()
    for pod in pods['items']:
        data.append({
            'name': pod['metadata']['name'],
            'id': pod['metadata']['uid'],
            'status': pod['status']['phase'],
        })

    data = KubeOperationQueryPodsData(items=data).dict()
    return GenericBaseResponse[list[KubeOperationQueryPodsData]](data=data)
