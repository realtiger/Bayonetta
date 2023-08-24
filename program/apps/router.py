from apps.admin.router import router as admin_router, tags_metadata as admin_tags_metadata
from apps.auth.router import router as auth_router, tags_metadata as auth_tags_metadata
from apps.index.router import router as index_router
from watchtower.settings import settings

routers = [
    {"router": index_router, "tags": ["index"]},
]

tags_metadata = [{"name": "index", "description": "Common operations. The **check health** / **login** logic is also here.", }, ]

if settings.AUTH_ENABLED:
    routers.append({"router": auth_router, "tags": ["auth"]})
    tags_metadata.extend(auth_tags_metadata)

if settings.ADMIN_ENABLED:
    routers.append({"router": admin_router})
    tags_metadata.extend(admin_tags_metadata)
