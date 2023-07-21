import json
import re
from calendar import timegm
from datetime import timedelta, datetime

from fastapi import status, Depends, Request
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from watchtower.depends.authorization.types import PayloadData, TokenType
from watchtower.depends.cache.cache import CacheSystem, cache
from watchtower.settings import settings, logger
from watchtower.status.global_status import StatusMap
from watchtower.status.types.exception import SiteException
from watchtower.status.types.response import Status, GenericBaseResponse

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

    # 生成payload
    # 过期时间
    payload.exp = timegm(expire.utctimetuple())
    # 生效时间
    payload.nbf = timegm((datetime.utcnow() - timedelta(seconds=10)).utctimetuple())
    # 签发时间
    payload.iat = timegm(datetime.utcnow().utctimetuple())
    # 签发者
    payload.iss = settings.SITE_NAME
    # 接收者
    payload.sub = subject.value
    payload.jti = f"{payload.aud}{payload.iat}"

    to_encode = {key: value for key, value in jsonable_encoder(payload).items() if value is not None}

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def signature_authentication(
        request: Request,
        security_scopes: SecurityScopes,
        token: str = Depends(oauth2_scheme),
        cache_client: CacheSystem = Depends(cache)
) -> PayloadData:
    """
    验证权限(必须登录)
    :param request: 请求对象，获取权限的时候需要根据当前访问方法获取url列表
    :param security_scopes: 权限范围
    :param token: 传入token
    :param cache_client: 缓存客户端
    :return: payload 信息
    """
    credentials_exception_headers = None
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
        credentials_exception_headers = {'WWW-Authenticate': authenticate_value}
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_aud": False})
        payload = PayloadData.parse_obj(payload)
        if payload.data and payload.data.id:
            # 如果有黑名单记录查看是否符合条件，符合条件则不允许登录
            blacklist = await cache_client.get_blacklist(payload.data.id)
            if blacklist:
                blacklist = PayloadData.parse_obj(json.loads(blacklist))
                if blacklist.nbf > payload.iat:
                    raise jwt.ExpiredSignatureError("token已经在黑名单中了")
        else:
            logger.info(f"jwt数据有问题 => {payload}/{token}")
            raise get_authorization_exception(status_item=StatusMap.INVALIDATE_CREDENTIALS, headers=credentials_exception_headers)
    except jwt.ExpiredSignatureError as e:
        logger.info(f"jwt 已经过期 => {token}[{e}]")
        raise get_authorization_exception(status_item=StatusMap.EXPIRED_CREDENTIALS)
    except (jwt.JWTError, ValidationError) as e:
        logger.info(f"jwt 数据处理有问题 => {token}[{e}]")
        raise get_authorization_exception(status_item=StatusMap.INVALIDATE_CREDENTIALS, headers=credentials_exception_headers)

    # 如果是超级管理员则不再进行权限验证，直接返回 payload 信息
    if payload.data.superuser:
        return payload

    # scopes权限验证
    can_active = payload.scopes
    for scope in security_scopes.scopes:
        # 方法权限有不能进入的项
        if scope not in can_active:
            logger.info(f"scope权限不足 => 安全权限:{security_scopes.scopes}/token申请权限:{can_active}")
            raise get_authorization_exception(status_item=StatusMap.SCOPE_NOT_AUTHORIZED, headers=credentials_exception_headers)

    # 访问方法及路径，路径需要去掉最后的/
    method = request.method.upper()
    path = request.url.path
    if path.endswith("/"):
        path = path[:-1]

    # 验证白名单列表，如果在白名单中则直接返回payload
    # TODO 白名单列表使用数据库存储
    for url_reg in settings.WEB_WHITE_TABLE.get(method, []):
        url_reg = f"^{url_reg}$"

        if re.match(url_reg, path):
            return payload

    # 获取权限缓存
    permissions = await cache_client.get_permission(payload.data.id, [method])
    if isinstance(permissions, str):
        permissions = json.loads(permissions)

    for url_reg in permissions:
        url_reg = f"^{url_reg}$"

        if re.match(url_reg, path):
            return payload

    response = GenericBaseResponse[dict](status=StatusMap.FORBIDDEN)
    raise SiteException(status_code=status.HTTP_403_FORBIDDEN, response=response)


async def optional_signature_authentication(
        request: Request,
        security_scopes: SecurityScopes,
        token: str = Depends(optional_oauth2_scheme),
        cache_client: CacheSystem = Depends(cache)
) -> PayloadData:
    """
    验证权限（可以不登录）
    :param request: 请求对象，获取权限的时候需要根据当前访问方法获取url列表
    :param security_scopes: 权限范围
    :param token: 传入token
    :param cache_client: 缓存客户端
    :return: payload 信息
    """
    payload = PayloadData()
    if token is not None:
        try:
            payload = await signature_authentication(request, security_scopes, token=token, cache_client=cache_client)
        except Exception as e:
            logger.warning(f"optional_signature_authentication => {e}")
    return payload
