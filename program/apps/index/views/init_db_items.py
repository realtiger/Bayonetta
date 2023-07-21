permission_list = [
    {"id": 1, "title": "获取所有用户", "url": "/api/admin/user", "method": "GET"},
    {"id": 2, "title": "创建单个用户", "url": "/api/admin/user", "method": "POST"},
    {"id": 3, "title": "删除多个用户", "url": "/api/admin/user", "method": "DELETE"},
    {"id": 4, "title": "获取单个用户", "url": r"/api/admin/user/\d+", "method": "GET"},
    {"id": 5, "title": "更新单个用户", "url": r"/api/admin/user/\d+", "method": "PUT"},
    {"id": 6, "title": "删除单个用户", "url": r"/api/admin/user/\d+", "method": "DELETE"},
]

menu_list = [
    {"id": 1, "title": "仪表盘", "link": "/dashboard", "icon": "user"},

    {"id": 2, "title": "系统管理", "link": "/manage", "icon": "user"},
    {"id": 3, "title": "用户管理", "link": "/manage/user", "icon": "user", "parent_id": 2, "permission_id": 1},
]
