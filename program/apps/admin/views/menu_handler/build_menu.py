from sqlalchemy import select

from apps.admin.models import Menu
from oracle.sqlalchemy import sql_helper
from oracle.types import ModelStatus
from watchtower.depends.cache.cache import cache as cache_client


def build_menu_tree(menu_dict: dict):
    tree = []
    for menu_id, menu in menu_dict.items():
        if menu['parent'] is None:
            tree.append(menu)
        else:
            parent = menu_dict.get(menu['parent'])
            if parent:
                if parent.get('children'):
                    parent['children'].append(menu)
                else:
                    parent['children'] = [menu]
    return tree


async def build():
    all_menu_statement = select(Menu).where(Menu.status == ModelStatus.ACTIVE).order_by(Menu.level.asc())
    async with sql_helper.get_session().begin() as session:
        menus = await session.execute(all_menu_statement)
        menus = menus.scalars().all()

    menu_dict = {}
    for menu in menus:
        menu_dict[menu.id] = {
            "id": menu.id,
            "parent": menu.parent,
            "title": menu.title,
            "icon": menu.icon,
            "hidden": menu.hidden,
            "level": menu.level,
            "status": menu.status.value,
            "create_time": str(menu.create_time),
            "update_time": str(menu.update_time),
        }
    return build_menu_tree(menu_dict)


async def set_menu_tree(menu: list):
    await cache_client.set_menu(value=menu)


async def get_menu_tree(refresh: bool = False):
    menu = await cache_client.get_menu()
    if menu is None or refresh:
        menu = await build()
        await set_menu_tree(menu)

    return menu
