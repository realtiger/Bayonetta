from pydantic import BaseModel, Field


class Menu(BaseModel):
    id: int = Field(default=None, description="菜单ID", title="菜单ID", example=1)
    title: str = Field(default=None, description="菜单标题", title="菜单标题", example="title")
    link: str = Field(default=None, description="菜单链接", title="菜单链接", example="link")
    icon: str = Field(default=None, description="菜单图标", title="菜单图标", example="menuIcon")
    parent: int = Field(default=None, description="父级菜单，0或者空为没有父级菜单", title="父级菜单", example=1)


class LoadData(BaseModel):
    app: str = Field(default=None, description="应用", title="应用", example="app")
    menu: list[Menu] = Field(default=list(), description="菜单列表", title="菜单列表", example=[Menu(id=1, title="title", link="link", icon="menuIcon", parent=1)])


class UserInfo(BaseModel):
    id: int | None = None
    name: str | None = None
    username: str | None = None
    email: str | None = None
    avatar: str | None = None
    superuser: bool = False
