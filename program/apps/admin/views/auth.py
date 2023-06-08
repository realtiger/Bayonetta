from datetime import timedelta, datetime

from fastapi import Depends, APIRouter, Request, Form
from fastapi.security import OAuth2PasswordRequestForm

from oracle import ModelStatus
from watchtower import generate_response_model, StatusMap, SiteException, Response, settings
from watchtower.depends.authorization import Token, verify_password, PayloadData, PayloadDataUserInfo, create_access_token, TokenType, signature_authentication
from watchtower.depends.cache import CacheSystem, cache

logger = settings.LOGGER

router = APIRouter()

IdentifyInvalid = generate_response_model("IdentifyInvalid", StatusMap.IDENTIFY_INVALID)
UserNotActive = generate_response_model("UserNotActive", StatusMap.USER_NOT_ACTIVE)
LoginFailed = generate_response_model("LoginFailed", StatusMap.LOGIN_FAILED)

IDENTIFY_INVALID_CODE = 400
LOGIN_FAILED_CODE = 540
USER_NOT_ACTIVE_CODE = 541

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
    401: {
        "model": IdentifyInvalid,
        "description": "认证失败",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.INVALIDATE_CREDENTIALS.code,
                    "success": StatusMap.INVALIDATE_CREDENTIALS.success,
                    "message": StatusMap.INVALIDATE_CREDENTIALS.message,
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


def get_user_info(username: str):
    """
    获取用户信息
    :param username:
    :return:
    """

    class User:
        username = ''
        password = ''
        status = ModelStatus.ACTIVE
        id = ''
        name = ''
        avatar = ''
        email = ''

    user = User()
    if username == 'admin':
        user.username = 'admin'
        user.password = '$2b$12$yu3rMjDKSRSkETz97HhsMuNs0IJB4A08qlG8QFMa152zy4HiijVba'
    return user


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
        # # 查找用户
        # user = await User.filter(username=form_data.username).first()
        if settings.ENV == "product":
            # TODO 补齐获取权限的功能
            scopes = ""
        else:
            scopes = form_data.scopes
        # TODO 测试用查找用户
        user = get_user_info(form_data.username)

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
            data = PayloadDataUserInfo(id=user.id, name=user.name, email=user.email, avatar=user.avatar, username=user.username)

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
                payload=PayloadData(scopes=scopes, data=data.dict(), aud=user.username),
                expires_delta=expires_delta,
                subject=TokenType.REFRESH_TOKEN
            )

            # TODO 存储权限
            await cache_client.set_permission(identify=user.id, value='all', expire=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

            if is_token:
                user.last_login_ip = login_ip
                user.last_login_time = datetime.now()
                # TODO 用户保存登录ip和登录时间
                # await user.save(update_fields=['last_login_ip', 'last_login_time'])
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
