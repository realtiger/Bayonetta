from fastapi import APIRouter, Depends

from apps.cmdb.views.server_handler.server import router as server_router, tags_metadata as server_tags_metadata
from oracle.utils import extend_tags_metadata
from watchtower import signature_authentication

router = APIRouter(prefix='/cmdb', dependencies=[Depends(signature_authentication)])

router.include_router(server_router, tags=['server'])

tags_metadata = extend_tags_metadata(server_tags_metadata)
