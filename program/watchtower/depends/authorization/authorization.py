from calendar import timegm
from datetime import timedelta, datetime

from fastapi import status, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from passlib.context import CryptContext

from .types import PayloadData, TokenType
from ...settings import settings
from ...status.global_status import StatusMap
from ...status.types.exception import SiteException
from ...status.types.response import Status, GenericBaseResponse

logger = settings.LOGGER

token_url = f"/{settings.URL_PREFIX.strip('/')}/login" if settings.URL_PREFIX else "/login"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_url)
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_url, auto_error=False)


def get_authorization_exception(status_item: Status, headers: dict | None = None) -> SiteException:
    response = GenericBaseResponse[dict]()
    response.update(status=status_item)

    if headers is None:
        headers = {"WWW-Authenticate": "Bearer"}

    return SiteException(status_code=status.HTTP_401_UNAUTHORIZED, response=response, headers=headers)


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_password_hash(password):
    return password_context.hash(password)


async def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


async def create_access_token(payload: PayloadData, expires_delta: timedelta = None, subject: TokenType = TokenType.TOKEN) -> str:
    """
    创建jwt格式token
    :param payload:
    :param expires_delta:
    :param subject:
    :return: token
    """
    if expires_delta is None:
        if settings.ACCESS_TOKEN_EXPIRE_MINUTES:
            expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expires_delta = timedelta(minutes=15)

    expire = datetime.utcnow() + expires_delta

    payload.exp = timegm(expire.utctimetuple())
    payload.nbf = timegm((datetime.utcnow() - timedelta(seconds=10)).utctimetuple())
    payload.iat = timegm(datetime.utcnow().utctimetuple())
    payload.iss = settings.SITE_NAME
    payload.sub = subject.value
    # 为以后黑名单禁用提前赋值标记
    payload.jti = f"{payload.aud}{payload.iat}"

    to_encode = {key: value for key, value in jsonable_encoder(payload).items() if value is not None}

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def signature_authentication(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)) -> PayloadData:
    """
    验证权限
    :param request:
    :param security_scopes:
    :param token: 传入token
    :return: payload 信息
    """
    credentials_exception_headers = None
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
        credentials_exception_headers = {'WWW-Authenticate': authenticate_value}
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        data = payload.get("data")
        if data and data.get('id'):
            pass
            # TODO 目前未实现
            # cache_client = await get_cache_client()
            # # 登录退出后将对应jti存储，不允许其他人登录。这里进行验证
            # # TODO 验证逻辑未完成
            # black_list = await redis_client.get(f"black_list_{payload.get('data').get('key')}")
            # if black_list:
            #     logger.error(black_list)
        else:
            logger.info(f"jwt数据有问题 => {payload}/{token}")
            raise get_authorization_exception(status_item=StatusMap.INVALIDATE_CREDENTIALS, headers=credentials_exception_headers)
    except jwt.ExpiredSignatureError:
        logger.info(f"jwt 已经过期 => {token}")
        raise get_authorization_exception(status_item=StatusMap.EXPIRED_CREDENTIALS)
    # except (JWTError, ValidationError):
    #     raise get_authorization_exception(status_item=StatusMap.INVALIDATE_CREDENTIALS, headers=credentials_exception_headers)
    # 全部可以进入的权限
    can_active = payload.get("scopes", [])
    for scope in security_scopes.scopes:
        # 方法权限有不能进入的项
        if scope not in can_active:
            logger.info(f"scope权限不足 => 安全权限:{security_scopes.scopes}/token申请权限:{can_active}")
            raise get_authorization_exception(status_item=StatusMap.SCOPE_NOT_AUTHORIZED, headers=credentials_exception_headers)
    if isinstance(payload, dict):
        payload = PayloadData(**payload)
    else:
        payload = PayloadData()
        logger.info(f"payload封装完成{payload}")
    return payload


async def optional_signature_authentication(security_scopes: SecurityScopes, token: str = Depends(optional_oauth2_scheme)):
    """
    验证权限
    :param request:
    :param security_scopes:
    :param token: 传入token
    :return: payload 信息
    """
    if token is None:
        payload = PayloadData()
    else:
        payload = await signature_authentication(security_scopes, token)
    return payload
