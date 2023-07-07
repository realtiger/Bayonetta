from apps.admin.router import router as admin_router, tags_metadata as admin_tags_metadata
from apps.auth.router import router as auth_router
from apps.index.router import router as index_router

routers = [
    {"router": index_router, "tags": ["index"]},
    {"router": auth_router, "tags": ["auth"]},
    {"router": admin_router},
]

tags_metadata = [{"name": "index", "description": "Common operations. The **check health** / **login** logic is also here.", }, ]
tags_metadata.extend(admin_tags_metadata)
