from pydantic import BaseModel, Field


class Permission(BaseModel):
    code: str = Field(default=None, description="权限代码", title="权限代码", example="")


class LoadData(BaseModel):
    app: str = Field(default=None, description="应用", title="应用", example="app")
    permissions: dict[str, list[Permission | bool]] = Field(default=dict(), description="权限列表", title="权限列表", example={'GET': Permission(code="app-permission")})
    auth: bool = Field(default=False, description="已经认证标志位", title="已经认证标志位", example=False)


class UserInfo(BaseModel):
    id: int | None = None
    name: str | None = None
    username: str | None = None
    email: str | None = None
    avatar: str | None = None
    superuser: bool = False
