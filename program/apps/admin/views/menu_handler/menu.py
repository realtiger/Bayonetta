from sqlalchemy import Update
from sqlalchemy.ext.declarative import DeclarativeMeta as Model

from apps.admin.models import Menu
from apps.admin.views.menu_handler.build_menu import get_menu_tree
from apps.admin.views.menu_handler.menu_type import MenuQueryData, MenuCreateData, MenuUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter
from watchtower import PayloadData
from watchtower.status.types.response import GetAllData, GenericBaseResponse, PaginationData


class MenuCRUDRouter(SQLAlchemyCRUDRouter):
    async def _create_validator(self, item: dict) -> dict:
        if "parent" in item and item["parent"] == 0:
            item.pop("parent")

        return item

    async def _post_create(self, model: Model) -> Model:
        await get_menu_tree(refresh=True)
        return model

    async def _post_update(self, model: Model) -> Model:
        await get_menu_tree(refresh=True)
        return model

    async def _post_delete(self, model: Model) -> Model:
        await get_menu_tree(refresh=True)
        return model

    async def _orm_update_statement(self, item_id: int, data: dict, payload: PayloadData | None = None) -> Update:
        # 非超级管理员用户无法修改状态
        if "status" in data:
            data.pop("status")

        return await super()._orm_update_statement(item_id, data, payload)


router = MenuCRUDRouter(
    MenuQueryData,
    Menu,
    MenuCreateData,
    MenuUpdateData,
    tags=['menu'],
    verbose_name='menu'
)
tags_metadata = [{"name": "menu", "description": "角色相关接口"}]


def get_all_menu_node(menu_list: list) -> list:
    all_node = []
    for menu in menu_list:
        all_node.append({
            'id': menu["id"],
            'title': menu["title"],
            'parent': menu["parent"],
            'icon': menu["icon"],
            'hidden': menu["hidden"],
            'level': menu["level"],
            'status': menu["status"],
            'create_time': menu["create_time"],
            'update_time': menu["update_time"],
            'is_parent': True if "children" in menu and menu['children'] else False,
        })

        if "children" in menu and menu["children"]:
            child_node = get_all_menu_node(menu["children"])
            all_node.extend(child_node)

    return all_node


@router.get("", summary="获取菜单", description="获取菜单", response_model=MenuQueryData)
async def get_menu():
    menus = await get_menu_tree()
    if menus:
        all_records = get_all_menu_node(menus)
    else:
        all_records = []

    all_records_count = len(all_records)
    pagination_data = PaginationData(index=1, limit=all_records_count, total=all_records_count, offset=0)
    data = GetAllData(items=all_records, pagination=pagination_data).dict()

    return GenericBaseResponse[GetAllData](data=data)
