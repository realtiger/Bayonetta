from fastapi import APIRouter
from pydantic import Field

from watchtower import Response

router = APIRouter()


class HealthResponse(Response[dict]):
    data: dict[str, str] = Field(default={"message": "Online!"})


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health():
    """
    健康检查，返回常量字符串
    \f
    :return:
    """
    return HealthResponse()
