from apps.admin.router import router as admin_router, tags_metadata as admin_tags_metadata
from apps.auth.router import router as auth_router, tags_metadata as auth_tags_metadata
from apps.cmdb.router import router as cmdb_router, tags_metadata as cmdb_tags_metadata, websocket_router
from apps.index.router import router as index_router
from apps.kube_dashboard.router import router as kube_router, tags_metadata as kube_tags_metadata
from watchtower.settings import settings

routers = [
    {"router": index_router, "tags": ["index"]},
]

tags_metadata = [{"name": "index", "description": "Common operations. The **check health** / **login** logic is also here.", }, ]

if settings.AUTH_MODULE_ENABLE:
    routers.append({"router": auth_router, "tags": ["auth"]})
    tags_metadata.extend(auth_tags_metadata)

if settings.ADMIN_MODULE_ENABLE:
    routers.append({"router": admin_router})
    tags_metadata.extend(admin_tags_metadata)

if settings.CMDB_MODULE_ENABLE:
    routers.extend([{"router": cmdb_router}, {"router": websocket_router}])
    tags_metadata.extend(cmdb_tags_metadata)

if settings.KUBE_DASHBOARD_MODULE_ENABLE:
    routers.append({"router": kube_router})
    tags_metadata.extend(kube_tags_metadata)
