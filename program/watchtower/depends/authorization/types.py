import enum

from pydantic import BaseModel, Field


class TokenType(enum.Enum):
    TOKEN = 'token'
    REFRESH_TOKEN = 'refresh_token'


class Token(BaseModel):
    access_token: str = Field(default="", example="access_token")
    refresh_token: str = Field(default="", example="refresh_token")
    token_type: str = Field(default="bearer")


class PayloadDataUserInfo(BaseModel):
    id: int | None = None
    name: str | None = None
    username: str | None = None
    email: str | None = None
    avatar: str | None = None
    superuser: bool = False


class PayloadData(BaseModel):
    """
    iss：Issuer 发行人
    sub：Subject 主题
    exp：Expiration time到期时间
    aud：Audience 用户
    nbf：Not before 在此之前不可用
    iat：Issued at 发布时间
    jti：JWT ID用于标识该JWT
    scopes:
    data: 自定义字段
    """
    iss: str | None = None
    sub: str | None = None
    exp: int | str | None = None
    # 可以访问的网站资源
    aud: list[str] | str | None = None
    nbf: int | str | None = None
    iat: int | str | None = None
    jti: str | None = None
    scopes: list[str] = []
    # PayloadDataUserInfo 类型的 dict
    data: PayloadDataUserInfo | None = None
