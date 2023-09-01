import enum

from sqlalchemy import String, Integer, Enum, ForeignKey, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oracle.sqlalchemy import SiteBaseModel


# 服务器类型
class ServerType(enum.Enum):
    Rack = "Rack"
    Blade = "Blade"
    Tower = "Tower"
    PC = "PC"
    Mini = "Mini"


# 添加方式，分为自动添加和手动添加
class CreatedBy(enum.Enum):
    Manual = "Manual"
    Auto = "Auto"


# 服务器标签关联表，多对多关系
class ServerToServerTag(SiteBaseModel):
    __tablename__ = "server_to_server_tag"

    server_id: Mapped[int] = mapped_column("server_id", BigInteger, ForeignKey("server.id", ondelete="CASCADE"), comment="服务器id")
    server_tag_id: Mapped[int] = mapped_column("server_tag_id", BigInteger, ForeignKey("server_tag.id", ondelete="CASCADE"), comment="服务器标签id")


# 服务器标签，通过标签来定义主机组
class ServerTag(SiteBaseModel):
    __tablename__ = "server_tag"

    name: Mapped[str] = mapped_column("name", String(512), comment="标签名称")
    detail: Mapped[str] = mapped_column("detail", String(512), comment="备注")

    servers = relationship("Server", secondary="server_to_server_tag", back_populates="server_tags")


# 服务器表
class Server(SiteBaseModel):
    __tablename__ = "server"

    name: Mapped[str] = mapped_column("name", String(512), comment="主机名称", unique=True)
    server_type: Mapped[ServerType] = mapped_column("server_type", Enum(ServerType), default=ServerType.Rack, comment="服务器类型")
    created_by: Mapped[CreatedBy] = mapped_column("created_by", Enum(CreatedBy), default=CreatedBy.Manual, comment="添加方式")
    manager_ip: Mapped[str] = mapped_column("manager_ip", String(128), comment="管理ip")
    private_ip: Mapped[str] = mapped_column("private_ip", String(128), comment="内网ip")
    public_ip: Mapped[str] = mapped_column("public_ip", String(128), comment="公网ip")
    port: Mapped[int] = mapped_column("port", Integer, comment="端口")
    idc: Mapped[str] = mapped_column("idc", String(128), comment="idc")
    admin_user: Mapped[str] = mapped_column("admin_user", String(128), comment="管理用户")
    region: Mapped[str] = mapped_column("region", String(128), comment="区域")
    detail: Mapped[str] = mapped_column("detail", String(128), comment="备注")

    server_tags = relationship("ServerTag", secondary="server_to_server_tag", back_populates="servers")
