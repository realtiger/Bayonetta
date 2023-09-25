from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from oracle.sqlalchemy import SiteBaseModel
from watchtower.settings import settings

if settings.KUBE_DASHBOARD_MODULE_ENABLE:
    class KubeSettings(SiteBaseModel):
        """
        kube 配置存储表
        """
        __tablename__ = "kube_settings"

        name: Mapped[str] = mapped_column("name", String(128), comment="配置名称")
        conf: Mapped[str] = mapped_column("conf", Text(), comment="配置内容")
        description: Mapped[str] = mapped_column("description", String(256), comment="配置描述")
