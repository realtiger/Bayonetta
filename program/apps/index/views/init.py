from fastapi import APIRouter
from pydantic import Field

from watchtower import Response

router = APIRouter()


class InitResponse(Response[dict]):
    data: dict[str, str] = Field(default={"message": "数据库初始化成功!"})


@router.get("/initDB/", response_model=InitResponse, summary="初始化数据库")
async def init_db():
    """
    初始化db数据库
    \f
    :return:
    """
    return InitResponse()
