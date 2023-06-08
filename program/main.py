from fastapi import Request

from watchtower.server import app


@app.get(
    "/",
    tags=['index'],
    summary="作用等同健康检查",
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {"message": "Hello World"}
                }
            },
            "description": '返回常量字符串 "Hello World" 表明系统正常',
        }
    }
)
async def root(request: Request):
    """
    作用等同健康检查，返回常量字符串 "Hello World" 判断系统已经正常启动
    \f
    :return:
    """
    return {"message": "Hello World"}
