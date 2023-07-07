from fastapi import APIRouter
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from apps.admin.models import User
from oracle.sqlalchemy import sql_helper
from watchtower import Response
from watchtower.depends.authorization.authorization import get_password_hash

router = APIRouter()


class InitResponse(Response[dict]):
    data: dict[str, str] = Field(default={"message": "数据库初始化成功!"})


@router.get("/initDB/", response_model=InitResponse, summary="初始化数据库")
async def init_db(force: bool = False):
    """
    初始化db数据库
    \f
    :return:
    """
    session_maker = sql_helper.get_session()
    async with session_maker.begin() as session:
        # # 新建用户
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

    return InitResponse()
