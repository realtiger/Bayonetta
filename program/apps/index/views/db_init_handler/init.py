from fastapi import APIRouter
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.admin.models import User, Role, Permission
from apps.index.views.db_init_handler import business_init
from apps.index.views.db_init_handler.init_db_items import permission_list
from oracle.sqlalchemy import sql_helper
from watchtower import Response
from watchtower.depends.authorization.authorization import get_password_hash
from watchtower.settings import settings

router = APIRouter()


class InitResponse(Response[dict]):
    data: dict[str, str] = Field(default={"message": "数据库初始化成功!"})


@router.get("/initDB/", response_model=InitResponse, summary="初始化数据库")
async def init_db(force: bool = False):
    """
    初始化db数据库
    \f
    :param force: 是否强制初始化
    :param business: 是否只初始化业务数据
    :return:
    """
    if settings.ADMIN_MODULE_ENABLE:
        session_maker = sql_helper.get_session()

        async with session_maker.begin() as session:
            # 新建角色
            select_role_statement = select(Role).where(Role.id == 1).options(selectinload(Role.permissions))
            admin_role = (await session.execute(select_role_statement)).scalar_one_or_none()
            if not admin_role:
                admin_role = Role(id=1, name="admin", detail="超级管理员", )
                session.add(admin_role)

            # 新建用户
            select_user_statement = select(User).where(User.id == 1).options(selectinload(User.roles))
            user = (await session.execute(select_user_statement)).scalar_one_or_none()
            password = "Bayonetta123"
            if not user:
                user = User(
                    id=1,
                    username="admin",
                    name="admin",
                    password=await get_password_hash(password.encode()),
                    email="user@example.com",
                    avatar="/assets/images/avatar/default.jpg",
                    detail="管理员用户",
                    superuser=True,
                )
                session.add(user)
            elif force:
                user.username = "admin"
                user.password = await get_password_hash(password.encode())
            user.roles.append(admin_role)
            await session.commit()
            await session.flush()

        async with session_maker.begin() as session:
            # ### 新建权限 ###
            # 从数据库中获取所有权限
            permission_ids = [permission["id"] for permission in permission_list]
            select_permission_statement = select(Permission).where(Permission.id.in_(permission_ids))
            exist_permissions = (await session.execute(select_permission_statement)).scalars().all()
            exist_permission_ids = [permission.id for permission in exist_permissions]

            # 只添加不存在的权限
            permissions = list()
            for permission in permission_list:
                if permission["id"] not in exist_permission_ids:
                    permissions.append(Permission(**permission))

            session.add_all(permissions)

            permissions.extend(exist_permissions)

            if permissions:
                admin_role = (await session.execute(select_role_statement)).scalar_one_or_none()
                for permission in permissions:
                    admin_role.permissions.append(permission)

            await session.commit()
            await session.flush()

    business_init.run()

    return InitResponse()
