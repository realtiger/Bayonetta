from pydantic import Field, BaseModel

from oracle.types import QueryBaseModel, UpdateAddFields


# ### 数据格式定义 ###
# 单个新建格式
class MenuCreateData(BaseModel):
    title: str = Field(description="菜单名称", title="菜单名称", example="menu-example", min_length=1)
    parent: int | None = Field(default=None, description="父级菜单id", title="父级菜单id", example=1)
    is_parent: bool = Field(default=False, description="是否为父级菜单", title="是否为父级菜单", example=False)
    icon: str = Field(default="", description="菜单图标", title="菜单图标", example="icon-menu")
    hidden: bool = Field(default=False, description="是否显示菜单", title="是否显示菜单", example=False)


# 单个更新格式
class MenuUpdateData(MenuCreateData, UpdateAddFields):
    pass


#  查询数据返回格式
class MenuQueryData(QueryBaseModel, MenuCreateData):
    pass
