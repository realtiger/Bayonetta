from fastapi import APIRouter, Depends

from apps.cmdb.views.server_handler.server import router as server_router, tags_metadata as server_tags_metadata
from apps.cmdb.views.server_handler.server_admin import router as server_admin_router, tags_metadata as server_admin_tags_metadata
from apps.cmdb.views.server_handler.terminal import router as terminal_router
from apps.cmdb.views.tag_handler.tag import router as tag_router, tags_metadata as tag_tags_metadata
from oracle.utils import extend_tags_metadata
from watchtower import signature_authentication

router = APIRouter(prefix='/cmdb', dependencies=[Depends(signature_authentication)])

router.include_router(server_router, tags=['server'])
router.include_router(tag_router)
router.include_router(server_admin_router, tags=['server-admin'])

tags_metadata = extend_tags_metadata(
    server_tags_metadata,
    tag_tags_metadata,
    server_admin_tags_metadata
)

websocket_router = APIRouter(prefix='/cmdb')
websocket_router.include_router(terminal_router)
