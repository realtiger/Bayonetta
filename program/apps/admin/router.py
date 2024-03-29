from fastapi import APIRouter, Depends

from apps.admin.views.menu_handler.menu import router as menu_router, tags_metadata as menu_tags_metadata
from apps.admin.views.operation_record_handler.operation_record import router as operation_record_router, tags_metadata as operation_record_tags_metadata
from apps.admin.views.permission_handler.permission import router as permission_router, tags_metadata as permission_tags_metadata
from apps.admin.views.role_handler.role import router as role_router, tags_metadata as role_tags_metadata
from apps.admin.views.user_handler.user import router as user_router, tags_metadata as user_tags_metadata
from oracle.utils import extend_tags_metadata
from watchtower import signature_authentication

router = APIRouter(prefix='/admin', dependencies=[Depends(signature_authentication)])

router.include_router(user_router, tags=['user'])
router.include_router(role_router, tags=['role'])
router.include_router(menu_router, tags=['menu'])
router.include_router(permission_router, tags=['permission'])
router.include_router(operation_record_router, tags=['operation'])

tags_metadata = extend_tags_metadata(user_tags_metadata, role_tags_metadata, menu_tags_metadata, permission_tags_metadata, operation_record_tags_metadata)
