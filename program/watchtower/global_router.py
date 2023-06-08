from apps import router

tags_metadata = router.tags_metadata if hasattr(router, "tags_metadata") else []
routers = router.routers if hasattr(router, "routers") else []
