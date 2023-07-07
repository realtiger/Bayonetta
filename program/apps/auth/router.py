from fastapi import APIRouter

from apps.auth.views.auth import router as auth_router

router = APIRouter()

router.include_router(auth_router, tags=['auth'])

tags_metadata = [{"name": "auth", "description": "认证处理", }]
