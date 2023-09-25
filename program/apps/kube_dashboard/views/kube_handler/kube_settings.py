from apps.kube_dashboard.models import KubeSettings
from apps.kube_dashboard.views.kube_handler.kube_settings_type import KubeSettingsQueryData, KubeSettingsCreateData, KubeSettingsUpdateData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter


class KubeSettingsCRUDRouter(SQLAlchemyCRUDRouter):
    pass


router = KubeSettingsCRUDRouter(
    KubeSettingsQueryData,
    KubeSettings,
    KubeSettingsCreateData,
    KubeSettingsUpdateData,
    tags=["kube-settings"],
    verbose_name='KubeSettings',
    # TODO 限制管理员登陆
    get_all_route=True
)
tags_metadata = [{"name": "kube-settings", "description": "k8s配置文件管理"}]
