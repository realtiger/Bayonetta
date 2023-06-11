from fastapi import APIRouter

from apps.admin.views.auth import router as auth_router
from apps.admin.views.operation_record import router as operation_record_router

router = APIRouter()

router.include_router(auth_router, tags=['auth'])
router.include_router(operation_record_router, tags=['operation'])

tags_metadata = [{"name": "auth", "description": "认证处理", }]
