from fastapi import APIRouter, Depends

from apps.admin.views.operation_record import router as operation_record_router
from apps.admin.views.role_handler.role import router as role_router, tags_metadata as role_tags_metadata
from apps.admin.views.user_handler.user import router as user_router, tags_metadata as user_tags_metadata
from watchtower import signature_authentication

router = APIRouter(prefix='/admin', dependencies=[Depends(signature_authentication)])

router.include_router(user_router, tags=['user'])
router.include_router(role_router, tags=['role'])
router.include_router(operation_record_router, tags=['operation'])

tags_metadata = []
tags_metadata.extend(user_tags_metadata)
tags_metadata.extend(role_tags_metadata)
