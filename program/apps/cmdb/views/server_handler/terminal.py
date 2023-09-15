import asyncio

import paramiko
from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy import select

from apps.cmdb.models import Server
from oracle.sqlalchemy import sql_helper
from oracle.types import ModelStatus
from watchtower import websocket_signature_authentication

router = APIRouter()


@router.websocket("/ws/{server_id}")
async def websocket_endpoint(websocket: WebSocket, server_id: str, payload=Depends(websocket_signature_authentication)):
    # 认证信息，用于验证用户是否有权限连接，怎么传递的，需要怎么传回去
    protocol = websocket.headers.get('Sec-WebSocket-Protocol')
    headers = [
        ('Sec-WebSocket-Protocol'.encode(), protocol.encode())
    ]

    await websocket.accept(headers=headers)
    server_info_statement = select(Server).filter(Server.id == server_id, Server.status == ModelStatus.ACTIVE)
    async with sql_helper.get_session().begin() as session:
        server_info = (await session.execute(server_info_statement)).scalar_one_or_none()

    if not server_info:
        await websocket.send_json({"message": f"没有找到服务器 {server_id}"})
        await websocket.close()
        return

    if not server_info.admin_user or not server_info.detail:
        await websocket.send_json({"message": f"服务器 {server_id} 没有配置管理员用户或者没有配置详情"})
        await websocket.close()
        return

    await websocket.send_json({"message": f"正在连接服务器 {server_id}"})
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server_info.private_ip, server_info.port, server_info.admin_user, server_info.detail)
    channel = ssh.invoke_shell(term='xterm')
    try:
        while True:
            output = ""
            data = await websocket.receive_json()
            command = data.get('message')
            if command:
                channel.send(command)
                while not channel.recv_ready():
                    await asyncio.sleep(0.1)
                while channel.recv_ready():
                    output = f"{output}{channel.recv(1024).decode()}"
            await websocket.send_json({"message": output})
    finally:
        channel.close()
        ssh.close()
