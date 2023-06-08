from fastapi import APIRouter

from apps.index.views.health import router as health_router
from apps.index.views.init import router as init_router

router = APIRouter()

router.include_router(init_router)
router.include_router(health_router)
