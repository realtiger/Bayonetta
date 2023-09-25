from fastapi import APIRouter, Depends

from apps.kube_dashboard.views.kube_handler.kube_operation import router as kube_operation_router, tags_metadata as kube_operation_tags_metadata
from apps.kube_dashboard.views.kube_handler.kube_settings import router as kube_settings_router, tags_metadata as kube_settings_tags_metadata
from oracle.utils import extend_tags_metadata
from watchtower import signature_authentication

router = APIRouter(prefix='/kube', dependencies=[Depends(signature_authentication)])

router.include_router(kube_settings_router)
router.include_router(kube_operation_router)

tags_metadata = extend_tags_metadata(kube_settings_tags_metadata, kube_operation_tags_metadata)
