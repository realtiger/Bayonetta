import enum

from sqlalchemy import String, Integer, Enum, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oracle.sqlalchemy import SiteBaseModel, ModelBase
from watchtower.settings import settings

if settings.CMDB_MODULE_ENABLE:
    # 服务器类型
    class ServerType(enum.Enum):
        Rack = "Rack"
        Blade = "Blade"
        Tower = "Tower"
        PC = "PC"
        Mini = "Mini"


    class CreatedBy(enum.Enum):
        """
        添加方式，分为自动添加和手动添加
        """
        Manual = "Manual"
        Auto = "Auto"


    class SystemType(enum.Enum):
        """
        操作系统类型
        """
        Linux = "Linux"
        Windows = "Windows"


    class SSHAuthType(enum.Enum):
        """
        ssh认证类型
        """
        Password = "Password"
        Key = "Key"


    class ServerToServerTag(ModelBase):
        """
        服务器标签关联表，多对多关系
        """
        __tablename__ = "server_to_server_tag"

        id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, comment="服务器标签关联表id")

        server_id: Mapped[int] = mapped_column("server_id", BigInteger, ForeignKey("server.id", ondelete="CASCADE"), comment="服务器id")
        server_tag_id: Mapped[int] = mapped_column("server_tag_id", BigInteger, ForeignKey("server_tag.id", ondelete="CASCADE"), comment="服务器标签id")

        __table_args__ = (
            UniqueConstraint("server_id", "server_tag_id", name="server_to_server_tag"),
        )


    class AssetUserToAssetUserGroup(ModelBase):
        """
        资产用户组关联表，多对多关系
        """
        __tablename__ = "asset_user_to_asset_user_group"

        id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, comment="资产用户组关联表id")

        asset_user_id: Mapped[int] = mapped_column("asset_user_id", BigInteger, ForeignKey("asset_user.id", ondelete="CASCADE"), comment="资产用户id")
        asset_user_group_id: Mapped[int] = mapped_column("asset_user_group_id", BigInteger, ForeignKey("asset_user_group.id", ondelete="CASCADE"), comment="资产用户组id")

        __table_args__ = (
            UniqueConstraint("asset_user_id", "asset_user_group_id", name="asset_user_to_asset_user_group"),
        )


    class RemoteUserToRemoteUserTag(ModelBase):
        """
        远程用户标签关联表，多对多关系
        """
        __tablename__ = "remote_user_to_remote_user_tag"

        id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, comment="远程用户标签关联表id")

        remote_user_id: Mapped[int] = mapped_column("remote_user_id", BigInteger, ForeignKey("remote_user.id", ondelete="CASCADE"), comment="远程用户id")
        remote_user_tag_id: Mapped[int] = mapped_column("remote_user_tag_id", BigInteger, ForeignKey("remote_user_tag.id", ondelete="CASCADE"), comment="远程用户标签id")

        __table_args__ = (
            UniqueConstraint("remote_user_id", "remote_user_tag_id", name="remote_user_to_remote_user_tag"),
        )


    class ServerTag(SiteBaseModel):
        """
        服务器标签，通过标签来定义主机组
        """
        __tablename__ = "server_tag"

        name: Mapped[str] = mapped_column("name", String(512), comment="标签名称")
        detail: Mapped[str] = mapped_column("detail", String(512), comment="备注")

        servers = relationship("Server", secondary="server_to_server_tag", back_populates="server_tags")
        user_server_remote_user_bindings = relationship("UserServerRemoteUserBinding", back_populates="server_tag")


    class RemoteUserTag(SiteBaseModel):
        """
        远程用户标签，通过标签来定义主机组
        """
        __tablename__ = "remote_user_tag"

        name: Mapped[str] = mapped_column("name", String(512), comment="标签名称")
        detail: Mapped[str] = mapped_column("detail", String(512), comment="备注")

        remote_users = relationship("RemoteUser", secondary="remote_user_to_remote_user_tag", back_populates="remote_user_tags")
        user_server_remote_user_bindings = relationship("UserServerRemoteUserBinding", back_populates="remote_user_tag")


    class RemoteUser(SiteBaseModel):
        """
        远程用户表
        可以登录服务器的用户
        """
        __tablename__ = "remote_user"

        name: Mapped[str] = mapped_column("name", String(512), comment="名称")
        username: Mapped[str] = mapped_column("username", String(512), comment="用户名")
        auth_type: Mapped[SSHAuthType] = mapped_column("auth_type", Enum(SSHAuthType), default=SSHAuthType.Password, comment="认证类型")
        # 如果是密码认证，则password字段存储密码，如果是密钥认证，则password字段存储密钥文件路径
        password: Mapped[str] = mapped_column("password", String(512), comment="密码")
        detail: Mapped[str] = mapped_column("detail", String(512), comment="备注")

        remote_user_tags = relationship("RemoteUserTag", secondary="remote_user_to_remote_user_tag", back_populates="remote_users")


    class ServerAdminInfo(SiteBaseModel):
        """
        服务器带外管理信息表
        目前仅支持ipmi
        """
        __tablename__ = "server_admin_info"

        name: Mapped[str] = mapped_column("name", String(512), comment="名称")
        ip: Mapped[str] = mapped_column("ip", String(512), comment="ip")
        username: Mapped[str] = mapped_column("username", String(512), comment="用户名")
        password: Mapped[str] = mapped_column("password", String(512), comment="密码")
        detail: Mapped[str] = mapped_column("detail", String(512), comment="备注")

        servers = relationship("Server", back_populates="server_admin_info")


    class Server(SiteBaseModel):
        """
        服务器表
        """
        __tablename__ = "server"

        name: Mapped[str] = mapped_column("name", String(512), comment="显示名称", unique=True)
        hostname: Mapped[str] = mapped_column("hostname", String(512), comment="主机名称")
        server_type: Mapped[ServerType] = mapped_column("server_type", Enum(ServerType), default=ServerType.Rack, comment="服务器类型")
        created_by: Mapped[CreatedBy] = mapped_column("created_by", Enum(CreatedBy), default=CreatedBy.Manual, comment="添加方式")
        system_type: Mapped[SystemType] = mapped_column("system_type", Enum(SystemType), default=SystemType.Linux, comment="操作系统类型")
        manager_ip: Mapped[str] = mapped_column("manager_ip", String(128), comment="管理ip")
        private_ip: Mapped[str] = mapped_column("private_ip", String(128), comment="内网ip")
        public_ip: Mapped[str] = mapped_column("public_ip", String(128), comment="公网ip")
        port: Mapped[int] = mapped_column("port", Integer, comment="登录端口", default=22)
        # TODO 之后优化为外键形式
        idc: Mapped[str] = mapped_column("idc", String(128), comment="idc")
        region: Mapped[str] = mapped_column("region", String(128), comment="区域")
        detail: Mapped[str] = mapped_column("detail", String(128), comment="备注")

        server_admin_info_id: Mapped[int] = mapped_column(
            "server_admin_info_id",
            BigInteger,
            ForeignKey("server_admin_info.id", ondelete="CASCADE"),
            comment="服务器管理信息id",
            nullable=True
        )

        server_admin_info = relationship("ServerAdminInfo", back_populates="servers")
        server_tags = relationship("ServerTag", secondary="server_to_server_tag", back_populates="servers")


    class AssetUser(SiteBaseModel):
        """
        资产用户表

        为了与用户表解耦，只存用户表id，不需保证用户表id存在
        """
        __tablename__ = "asset_user"

        user_id: Mapped[int] = mapped_column("user_id", BigInteger, comment="用户id")
        detail: Mapped[str] = mapped_column("detail", String(512), comment="备注")

        asset_user_groups = relationship("AssetUserGroup", secondary="asset_user_to_asset_user_group", back_populates="asset_users")
        user_server_remote_user_bindings = relationship("UserServerRemoteUserBinding", back_populates="asset_user")


    class AssetUserGroup(SiteBaseModel):
        """
        资产用户组表
        """
        __tablename__ = "asset_user_group"

        name: Mapped[str] = mapped_column("name", String(512), comment="名称")
        detail: Mapped[str] = mapped_column("detail", String(512), comment="备注")

        asset_users = relationship("AssetUser", secondary="asset_user_to_asset_user_group", back_populates="asset_user_groups")


    class UserServerRemoteUserBinding(SiteBaseModel):
        """
        用户-服务器-账号绑定表
        """
        __tablename__ = "user_server_remote_user_binding"

        __table_args__ = (
            # 联合唯一索引
            UniqueConstraint("asset_user_id", "server_tag_id", "remote_user_tag_id", name="user_server_remote_user_binding"),
        )

        asset_user_id: Mapped[int] = mapped_column("asset_user_id", BigInteger, ForeignKey("asset_user.id", ondelete="CASCADE"), comment="资产用户id")
        server_tag_id: Mapped[int] = mapped_column("server_tag_id", BigInteger, ForeignKey("server_tag.id", ondelete="CASCADE"), comment="服务器标签id")
        remote_user_tag_id: Mapped[int] = mapped_column("remote_user_tag_id", BigInteger, ForeignKey("remote_user_tag.id", ondelete="CASCADE"), comment="远程用户标签id")

        asset_user = relationship("AssetUser", back_populates="user_server_remote_user_bindings")
        server_tag = relationship("ServerTag", back_populates="user_server_remote_user_bindings")
        remote_user_tag = relationship("RemoteUserTag", back_populates="user_server_remote_user_bindings")
