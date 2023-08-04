import datetime
import enum

from sqlalchemy import String, BigInteger, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oracle.sqlalchemy import SiteBaseModel, ModelBase


class PermissionMethods(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class UserRole(ModelBase):
    __tablename__ = "user_role"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, comment="用户角色关联表id")
    # user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("user.id"), comment="用户id")
    # 添加级联删除
    user_id: Mapped[int] = mapped_column("user_id", BigInteger, ForeignKey("user.id", ondelete="CASCADE"), comment="用户id")
    role_id: Mapped[int] = mapped_column("role_id", BigInteger, ForeignKey("role.id", ondelete="CASCADE"), comment="角色id")


class RolePermission(ModelBase):
    __tablename__ = "role_permission"

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, comment="角色权限关联表id")
    role_id: Mapped[int] = mapped_column("role_id", BigInteger, ForeignKey("role.id", ondelete="CASCADE"), comment="角色id")
    permission_id: Mapped[int] = mapped_column("permission_id", BigInteger, ForeignKey("permission.id", ondelete="CASCADE"), comment="权限id")


# 角色表
class Role(SiteBaseModel):
    __tablename__ = "role"

    name: Mapped[str] = mapped_column("name", String(128), comment="角色名称", unique=True)
    detail: Mapped[str] = mapped_column("detail", String(128), default="", comment="角色简介")

    users = relationship("User", secondary="user_role", back_populates="roles")
    permissions = relationship("Permission", secondary="role_permission", back_populates="roles")


# 用户表
class User(SiteBaseModel):
    __tablename__ = "user"

    username: Mapped[str] = mapped_column("username", String(128), comment="用户登录名", unique=True)
    password: Mapped[str] = mapped_column("password", String(128), comment="用户密码")
    name: Mapped[str] = mapped_column("name", String(128), default="name", comment="用户展示名称，可以修改")
    avatar: Mapped[str] = mapped_column("avatar", String(128), default="", comment="头像信息，记录头像的url值")
    detail: Mapped[str] = mapped_column("detail", String(128), default="", comment="用户简介，将要介绍用户")
    email: Mapped[str] = mapped_column("email", String(128), unique=True, comment="用户邮箱")
    superuser: Mapped[bool] = mapped_column("superuser", String(128), default=False, comment="是否是超级管理员")
    last_login_ip: Mapped[str] = mapped_column("last_login_ip", String(128), comment="最近一次登录ip", default="0.0.0.0")
    last_login_time: Mapped[str] = mapped_column("last_login_time", String(128), comment="最近一次登录时间", default=datetime.datetime.now)

    roles = relationship("Role", secondary="user_role", back_populates="users")


class Permission(SiteBaseModel):
    __tablename__ = "permission"

    title: Mapped[str] = mapped_column("title", String(128), comment="权限名称", unique=True)
    url: Mapped[str] = mapped_column("url", String(256), comment="权限url")
    method: Mapped[PermissionMethods] = mapped_column("method", Enum(PermissionMethods), default=PermissionMethods.GET, comment="权限请求方法")
    code: Mapped[str] = mapped_column("code", String(128), comment="权限代码")

    roles = relationship("Role", secondary="role_permission", back_populates="permissions")

    __table_args__ = (
        # 联合唯一索引
        UniqueConstraint("url", "method", name="url_method"),
    )


# 操作记录
class OperationRecord(SiteBaseModel):
    __tablename__ = "operation_record"

    user_id: Mapped[int] = mapped_column("user_id", BigInteger, comment="用户id")
    data: Mapped[str] = mapped_column("data", String(512), comment="请求数据")
