from fastapi import APIRouter

from apps.index.views.health import router as health_router
from apps.index.views.db_init_handler.init import router as init_router
from watchtower.settings import settings

router = APIRouter()

if settings.ADMIN_MODULE_ENABLE:
    router.include_router(init_router)

router.include_router(health_router)
