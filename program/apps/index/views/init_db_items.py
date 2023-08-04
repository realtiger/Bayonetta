permission_list = [
    {"id": 1, "title": "获取所有用户", "url": "/api/admin/user", "method": "GET", "code": "system:get-all-user"},
    {"id": 2, "title": "创建单个用户", "url": "/api/admin/user", "method": "POST", "code": "system:create-one-user"},
    {"id": 3, "title": "删除多个用户", "url": "/api/admin/user", "method": "DELETE", "code": "system:delete-many-user"},
    {"id": 4, "title": "获取单个用户", "url": r"/api/admin/user/\d+", "method": "GET", "code": "system:get-one-user"},
    {"id": 5, "title": "更新单个用户", "url": r"/api/admin/user/\d+", "method": "PUT", "code": "system:update-one-user"},
    {"id": 6, "title": "删除单个用户", "url": r"/api/admin/user/\d+", "method": "DELETE", "code": "system:delete-one-user"},
    {"id": 7, "title": "获取所有角色", "url": "/api/admin/role", "method": "GET", "code": "system:get-all-role"},
    {"id": 8, "title": "创建单个角色", "url": "/api/admin/role", "method": "POST", "code": "system:create-one-role"},
    {"id": 9, "title": "删除多个角色", "url": "/api/admin/role", "method": "DELETE", "code": "system:delete-many-role"},
    {"id": 10, "title": "获取单个角色", "url": r"/api/admin/role/\d+", "method": "GET", "code": "system:get-one-role"},
    {"id": 11, "title": "更新单个角色", "url": r"/api/admin/role/\d+", "method": "PUT", "code": "system:update-one-role"},
    {"id": 12, "title": "删除单个角色", "url": r"/api/admin/role/\d+", "method": "DELETE", "code": "system:delete-one-role"},
]
