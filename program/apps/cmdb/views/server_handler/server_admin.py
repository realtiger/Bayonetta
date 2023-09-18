from subprocess import Popen, PIPE, STDOUT

from fastapi import Request, Depends
from sqlalchemy import select

from apps.admin.views.operation_record_handler.utils import save_operation_record
from apps.cmdb.models import ServerAdminInfo
from apps.cmdb.views.server_handler.server_admin_type import ServerAdminQueryData, ServerAdminCreateData, ServerAdminUpdateData, ServerAdminOperationData, \
    ServerAdminInfoOperationResponseData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter
from oracle.types import ITEM_NOT_FOUND_CODE
from watchtower import PayloadData, signature_authentication, SiteException
from watchtower.settings import logger
from watchtower.status.global_status import StatusMap
from watchtower.status.types.response import Status, GenericBaseResponse


def build_ipmitool_cmd(host, username, password, cmd):
    return f"ipmitool -I lanplus -H {host} -U {username} -P {password} {cmd}"


def run_ipmitool(cmd):
    child = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT)
    output, _ = child.communicate()
    return output.decode(), child.returncode


class ServerAdminCRUDRouter(SQLAlchemyCRUDRouter):
    app = 'cmdb'
    module = 'server_admin'

    async def _post_create(self, item, request: Request | None = None, payload: PayloadData | None = None):
        # 记录新建主机管理信息，并且记录时出错不影响用户正常添加
        try:
            message = f"新建主机标签: {item}"
            await save_operation_record(request, self.app, self.module, payload, message)
        except Exception as error:
            logger.error(f"记录新建主机记录时出错: {error}")

    async def _post_update(self, item: dict, original_data: dict, request: Request | None = None, payload: PayloadData | None = None) -> dict:
        message = f"更新前数据: {original_data}, 更新后数据: {item}"
        # 记录更新主机，并且记录时出错不影响用户正常更新
        try:
            await save_operation_record(request, self.app, self.module, payload, message)
        except Exception as error:
            logger.error(f"记录更新主机记录时出错: {error}")

        return item

    async def _post_delete(self, item: dict, request: Request | None = None, payload: PayloadData | None = None) -> dict:
        message = f"删除数据: {item}"
        # 记录删除主机，并且记录时出错不影响用户正常删除
        try:
            await save_operation_record(request, self.app, self.module, payload, message)
        except Exception as error:
            logger.error(f"记录删除主机记录时出错: {error}")

        return item


router = ServerAdminCRUDRouter(
    ServerAdminQueryData,
    ServerAdminInfo,
    ServerAdminCreateData,
    ServerAdminUpdateData,
    tags=['server_admin_info'],
    verbose_name='server_admin',
    delete_all_route=True
)
tags_metadata = [{"name": "server_admin", "description": "主机管理信息"}]


@router.post('/exec/{item_id}', summary="修改主机标签", description="修改主机标签", response_model=ServerAdminInfoOperationResponseData)
async def update_server_admin_info(item_id: int, operation_data: ServerAdminOperationData, payload: PayloadData = Depends(signature_authentication)):
    """
    修改主机标签
    :param operation_data:
    :param item_id: 主机管理信息id
    :param payload: 用户信息
    :param request: 请求信息
    :return: 主机管理信息
    """
    select_server_admin_info_statement = select(ServerAdminInfo).where(ServerAdminInfo.id == item_id)
    async with router.db_func().begin() as session:
        server_admin_info = await session.execute(select_server_admin_info_statement)
        server_admin_info = server_admin_info.scalar_one_or_none()
        if not server_admin_info:
            status = Status(code=StatusMap.ITEM_NOT_FOUND.code, message="没有找到主机管理信息")
            response = GenericBaseResponse[dict](status=status)
            raise SiteException(status_code=ITEM_NOT_FOUND_CODE, response=response) from None
        host = server_admin_info.ip
        username = server_admin_info.username
        password = server_admin_info.password

    output = ""
    code = 0
    match operation_data.operation:
        case "status":
            cmd = build_ipmitool_cmd(host, username, password, "power status")
            output, code = run_ipmitool(cmd)

    data = ServerAdminInfoOperationResponseData(operation=operation_data.operation, output=output, code=code)
    return GenericBaseResponse[ServerAdminInfoOperationResponseData](data=data)
