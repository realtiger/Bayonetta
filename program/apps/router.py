from apps.index.router import router as index_router
from apps.admin.router import router as admin_router, tags_metadata as admin_tags_metadata

routers = [{"router": index_router, "tags": ["index"]}, {"router": admin_router}]

tags_metadata = [{"name": "index", "description": "Common operations. The **check health** / **login** logic is also here.", }, ]
tags_metadata.extend(admin_tags_metadata)
