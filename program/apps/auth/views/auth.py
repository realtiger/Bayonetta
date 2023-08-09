from calendar import timegm
from datetime import timedelta, datetime

from fastapi import Depends, APIRouter, Request, Form
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes
from sqlalchemy import select

from apps.admin.models import User, Role, Permission, PermissionMethods
from apps.auth.views.auth_types import LoadData, UserInfo
from oracle.sqlalchemy import sql_helper
from oracle.types import ModelStatus
from watchtower import generate_response_model, SiteException, Response, settings
from watchtower.depends.authorization.authorization import verify_password, create_access_token, signature_authentication, optional_signature_authentication
from watchtower.depends.authorization.types import Token, PayloadData, PayloadDataUserInfo, TokenType
from watchtower.depends.cache.cache import CacheSystem, cache
from watchtower.settings import settings, logger
from watchtower.status.global_status import StatusMap

router = APIRouter()

IdentifyInvalid = generate_response_model("IdentifyInvalid", StatusMap.IDENTIFY_INVALID)
UserNotActive = generate_response_model("UserNotActive", StatusMap.USER_NOT_ACTIVE)
LoginFailed = generate_response_model("LoginFailed", StatusMap.LOGIN_FAILED)

IDENTIFY_INVALID_CODE = 261
LOGIN_FAILED_CODE = 262
USER_NOT_ACTIVE_CODE = 263

login_responses = {
    IDENTIFY_INVALID_CODE: {
        "model": IdentifyInvalid,
        "description": "登录信息错误",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.IDENTIFY_INVALID.code,
                    "success": StatusMap.IDENTIFY_INVALID.success,
                    "message": StatusMap.IDENTIFY_INVALID.message,
                    "data": {}
                }
            }
        }
    },
    LOGIN_FAILED_CODE: {
        "model": LoginFailed,
        "description": "登录失败，服务器错误",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.USER_NOT_ACTIVE.code,
                    "success": StatusMap.USER_NOT_ACTIVE.success,
                    "message": StatusMap.USER_NOT_ACTIVE.message,
                    "data": {}
                }
            }
        }
    },
    USER_NOT_ACTIVE_CODE: {
        "model": UserNotActive,
        "description": "用户状态异常",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.LOGIN_FAILED.code,
                    "success": StatusMap.LOGIN_FAILED.success,
                    "message": StatusMap.LOGIN_FAILED.message,
                    "data": {}
                }
            }
        }
    },
}


class OAuth2RequestForm(OAuth2PasswordRequestForm):
    def __init__(
            self,
            grant_type: str = Form(default=None, regex="password"),
            username: str = Form(),
            password: str = Form(),
            scope: str = Form(default=""),
            client_id: str | None = Form(default=None),
            client_secret: str | None = Form(default=None),
            remember: bool = Form(default=False)
    ):
        super().__init__(grant_type, username, password, scope, client_id, client_secret)
        self.remember = remember


async def get_user_info(username: str) -> User | None:
    """
    获取用户信息
    :param username: 查找用户的用户名
    :return: User
    """
    select_user_statement = select(User).where(User.username == username)
    async with sql_helper.get_session().begin() as session:
        user = (await session.execute(select_user_statement)).scalar_one_or_none()

    return user


async def get_permissions_by_user_id(user_id: int) -> dict[str, list[str]]:
    """
    通过用户id获取权限和菜单，菜单信息作为权限的一部分返回
    :param user_id: 用户id
    :return: 权限列表
    """
    permissions = {method: list() for method in PermissionMethods.__members__.keys()}

    # 获取用户权限的sql语句
    select_permissions_statement = select(Permission.id, Permission.method, Permission.url, Permission.code).join(User.roles).join(Role.permissions) \
        .where(User.id == user_id, Permission.status == ModelStatus.ACTIVE).distinct()
    async with sql_helper.get_session().begin() as session:
        permission_queryset = (await session.execute(select_permissions_statement)).all()

    for permission in permission_queryset:
        permissions[permission.method.name].append({
            "id": permission.id,
            "url": permission.url,
            "code": permission.code
        })

    return permissions


async def generate_token(form_data: OAuth2RequestForm, cache_client: CacheSystem, login_ip: str = "0.0.0.0", is_token: bool = True):
    """
    生成token
    :param form_data: 表单数据
    :param cache_client: 缓存客户端
    :param login_ip: 登录ip
    :param is_token: 是否是登录时生成token
                True:登录生成Token
                False:刷新token直接生成token
    :return:
    """
    response = Response[dict]()
    access_token = refresh_token = ""
    try:
        if settings.ENV == "product":
            # TODO 补齐获取权限的功能
            scopes = ""
        else:
            scopes = form_data.scopes

        user = await get_user_info(form_data.username)

        # 用户认证是否通过标志位
        is_auth = False
        if user:
            if is_token:
                is_auth = await verify_password(form_data.password, user.password)
            else:
                is_auth = True

        if is_auth:
            # 未激活状态报错
            if user.status != ModelStatus.ACTIVE:
                response.update(status=StatusMap.USER_NOT_ACTIVE)
                raise SiteException(status_code=USER_NOT_ACTIVE_CODE, response=response)

            # 获取用户基本信息
            data = PayloadDataUserInfo(id=user.id, name=user.name, email=user.email, avatar=user.avatar, username=user.username, superuser=user.superuser)

            # 记住密码或者刷新token时设置过期时间,否则不设置过期时间
            if form_data.remember or not is_token:
                # 过期时间最小为1周
                expires_delta = timedelta(weeks=1)
                # 判断过期时间是否设置,如果设置了且两倍的过期时间大于1周,则过期时间设置为两倍的设置时间
                if settings.ACCESS_TOKEN_EXPIRE_MINUTES:
                    # 两倍的过期时间
                    double_access_token_expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 2)
                    if expires_delta < double_access_token_expires_delta:
                        expires_delta = double_access_token_expires_delta
            else:
                expires_delta = None

            access_token = await create_access_token(payload=PayloadData(scopes=scopes, data=data, aud=user.username))
            refresh_token = await create_access_token(
                payload=PayloadData(scopes=scopes, data=data, aud=user.username),
                expires_delta=expires_delta,
                subject=TokenType.REFRESH_TOKEN
            )

            # 获取权限信息和菜单，然后存储到缓存中
            permissions = await get_permissions_by_user_id(user.id)

            # 如果权限为空，则删除该key，即空访问方法
            permissions = {method: permissions[method] for method in permissions if permissions[method]}
            # 是否是超级管理员的信息也存储到权限信息中
            permissions["superuser"] = [user.superuser]

            await cache_client.set_permission(identify=user.id, permissions=permissions, expire=expires_delta if expires_delta else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

            if is_token:
                # 用户保存登录ip和登录时间
                user.last_login_ip = login_ip
                user.last_login_time = datetime.now()
                async with sql_helper.get_session().begin() as session:
                    await session.merge(user)

    except SiteException as error:
        logger.error(f"用户登录错误，错误原因为：{error.response.message}")
        raise error
    except Exception as error:
        logger.error(f"逻辑错误，错误原因为：{error}")
        response.update(status=StatusMap.LOGIN_FAILED)
        raise SiteException(status_code=LOGIN_FAILED_CODE, response=response)

    return access_token, refresh_token


@router.post(
    "/login",
    response_model=Token,
    summary="登录接口，获取token",
    responses=login_responses
)
async def login(request: Request, form_data: OAuth2RequestForm = Depends(), cache_client: CacheSystem = Depends(cache)):
    """
    OAUTH2方式的token获取方式，返回格式仅为token格式
    \f
    :param request: 请求对象
    :param form_data: 表单数据
    :param cache_client: 缓存客户端
    :return:
    """
    response_data = Token()

    # TODO 未验证转发情况的客户端ip
    login_ip = request.client.host
    # 获取token
    access_token, refresh_token = await generate_token(form_data, cache_client=cache_client, login_ip=login_ip)

    # 获取到说明一切正常
    if access_token:
        response_data.access_token = access_token
        response_data.refresh_token = refresh_token
    # 获取不到说明认证出错
    else:
        response = Response[dict]()
        response.update(StatusMap.IDENTIFY_INVALID)
        raise SiteException(status_code=IDENTIFY_INVALID_CODE, response=response, headers={"WWW-Authenticate": "Bearer"})
    return response_data


@router.post(
    "/refresh",
    response_model=Token,
    summary="登录接口，获取token",
    responses=login_responses
)
async def refresh(payload: PayloadData = Depends(signature_authentication), cache_client: CacheSystem = Depends(cache)):
    """
    刷新 token
    \f
    :param payload: token 负载数据
    :param cache_client: 缓存客户端
    :return:
    """
    response_data = Token()

    if payload.sub == TokenType.REFRESH_TOKEN.value:
        form_data = OAuth2RequestForm(username=payload.data.username, password='', scope=','.join(payload.scopes))
        # 获取token
        access_token, refresh_token = await generate_token(form_data, cache_client, is_token=False)

        # 获取到说明一切正常
        if access_token:
            response_data.access_token = access_token
            response_data.refresh_token = refresh_token
            return response_data
        logger.error(f"刷新token失败，获取到的token为空，payload为：{payload}")
    response = Response()
    response.update(StatusMap.IDENTIFY_INVALID)
    raise SiteException(status_code=IDENTIFY_INVALID_CODE, response=response)


@router.post(
    "/logout",
    response_model=Response,
    summary="登出接口，清除token"
)
async def logout(payload: PayloadData = Depends(optional_signature_authentication), cache_client: CacheSystem = Depends(cache)):
    """
    登出接口，清除token
    \f
    :param payload: token 负载数据
    :param cache_client: 缓存客户端
    :return:
    """
    if payload.data:
        expire = payload.exp - timegm(datetime.utcnow().utctimetuple())
        await cache_client.set_blacklist(identify=payload.data.id, value=payload.json(), expire=expire)
        await cache_client.delete_permission(identify=payload.data.id)
    return Response[dict]()


@router.get("/load_data", summary="加载数据", response_model=Response[LoadData])
async def load_init_data(request: Request, payload: PayloadData = Depends(optional_signature_authentication), cache_client: CacheSystem = Depends(cache)):
    load_data = LoadData()
    if not payload.data:
        token = request.headers.get("Authorization-Refresh", None)
        if token:
            payload = await optional_signature_authentication(request, SecurityScopes(), token, cache_client)

    if payload.data:
        load_data.auth = True
        methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        # permission是 list[{ 'id': int, 'url': str, 'code': str}] 的形式
        permissions = await cache_client.get_permission(payload.data.id, methods)
        if permissions:
            for index in range(len(methods)):
                method = methods[index]
                permission = permissions[index]
                if permission:
                    load_data.permissions[method] = [p.get('code') for p in permission]
    else:
        load_data.permissions = {}
        load_data.auth = False

    return Response[LoadData](data=load_data)


@router.get("/user/info", summary="获取用户信息", response_model=Response[UserInfo])
async def get_user_info_handler(payload: PayloadData = Depends(signature_authentication)):
    """
    获取用户信息
    \f
    :param payload: token 负载数据
    :return:
    """
    user_info = payload.data
    return Response[UserInfo](data=user_info)
