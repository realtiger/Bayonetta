import logging
import logging.config
import random
import string
from pathlib import Path

from pydantic import BaseSettings

from watchtower.settings.logger_config import get_logging_dict, ColorFormatter

BASE_DIR = Path(__file__).parent.parent.parent
PROJECT_NAME = BASE_DIR.name
SITE_NAME = PROJECT_NAME
# TODO 目前写死，后期修改为主机名、MAC地址hash计算
SERVER_ID = 0
DATACENTER_ID = 0
STATIC_URL = "/static"
STATIC_PATH = BASE_DIR / "static"
ENV = "develop"


# TODO 简单实现，只为了完成功能
def gen_secret_key() -> list:
    chars = list()
    chars.extend(string.ascii_letters)
    chars.extend(string.digits)

    secret_key = list()
    for i in range(64):
        secret_key.append(random.choice(chars))
    return secret_key


class Settings(BaseSettings):
    """
    基础配置
    """
    SITE_NAME: str = SITE_NAME
    BASE_DIR: Path = BASE_DIR
    PROJECT_NAME: str = PROJECT_NAME
    SERVER_ID: int = SERVER_ID
    DATACENTER_ID: int = DATACENTER_ID
    STATIC_URL: str = STATIC_URL
    STATIC_PATH: Path = STATIC_PATH
    ENV: str = ENV
    SECRET_KEY: str = "".join(gen_secret_key())
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # 全局路由前缀
    URL_PREFIX: str = ''

    """
    跨域配置
    """
    # **一个**正则表达式字符串，匹配的源允许跨域请求，例如 'https://.*\.example\.org'。
    CORS_ALLOW_ORIGIN_REGEX: str = None
    # 允许的源列表（由字符串组成），先匹配正则
    CORS_ALLOW_ORIGINS: list[str] = []
    # 允许跨域请求支持 cookies。默认是 False。
    # 允许凭证时 allow_origins 不能设定为 ['*']，必须指定源。
    CORS_ALLOW_CREDENTIALS: bool = False
    # 允许的 HTTP 方法（POST，PUT）或者使用通配符 "*" 允许所有方法。默认为 ['GET']。
    CORS_ALLOW_METHODS: list[str] = ['GET']
    # 允许的 HTTP headers 或者使用通配符 "*" 允许所有 headers。默认为 []。
    CORS_ALLOW_HEADERS: list[str] = []
    # 浏览器访问的响应头。默认为 []。
    CORS_EXPOSE_HEADERS: list[str] = []
    # 浏览器缓存 CORS 响应的最长时间，单位是秒。默认为 600
    CORS_MAX_AGE: int = 600

    """
    docs（swagger）文档设置
    """
    OPENAPI_URL: str = "/openapi.json"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    SITE_TITLE: str = "平台"
    SITE_DESCRIPTION: str = SITE_TITLE
    DOCS_VERSION: str = "2207"
    SWAGGER_FAVICON_URL: str = ""
    SWAGGER_JS_URL: str = ""
    SWAGGER_CSS_URL: str = ""
    REDOC_FAVICON_RUL: str = ""
    REDOC_JS_RUL: str = ""
    TERMS_OF_SERVICE: str = ""
    # CONTACT = {
    #     "name": "",
    #     "url": "",
    #     "email": "",
    # }
    CONTACT: dict = None
    # LICENSE_INFO = {
    #     "name": "",
    #     "url": "",
    # }
    LICENSE_INFO: dict = None

    """
    web设置
    """
    WEB_TITLE: str = SITE_TITLE
    WEB_DESCRIPTION: str = SITE_DESCRIPTION
    WEB_VERSION: str = DOCS_VERSION
    WEB_WHITE_TABLE: dict[str, list[str]] = {
        'GET': [
            '/api/logout',
            '/api/load_data',
            '/api/user/info',
        ],
        'POST': [
            '/api/login',
            '/api/refresh'
        ]
    }

    """
    database设置
    """
    DB_ENABLE: bool = False
    DB_ENGINE: str = 'tortoise.backends.mysql'
    DB_HOST: str = '127.0.0.1'
    DB_PORT: int = 3306
    DB_USER: str = 'username'
    DB_PASSWORD: str = 'password'
    DB_DATABASE: str = 'master'
    DB_MINSIZE: int = 1
    DB_MAXSIZE: int = 5
    DB_CHARSET: str = 'utf8mb4'
    DB_ECHO: bool = True
    # DB_USE_TZ: bool = False
    # DB_TIMEZONE: str = 'Asia/Shanghai'

    """
    redis设置
    """
    CACHE_REDIS_ENABLE: bool = False
    CACHE_REDIS_HOST: str = '127.0.0.1'
    CACHE_REDIS_PORT: str = '6379'
    CACHE_REDIS_DB: str = '8'
    CACHE_REDIS_CHARSET: str = 'utf-8'
    CACHE_REDIS_USERNAME: str = ''
    CACHE_REDIS_PASSWORD: str = ''

    """
    日志设置
    """
    LOG_LEVEL: str = 'DEBUG'
    LOG_DIR: str = 'logs'

    LOGGER: logging.Logger = None

    """
    自关闭设置
    """
    # 是否进行开启，目前仅支持使用supervisor启动的程序
    SELF_CLOSE_ENABLE: bool = False
    # 多长时间未访问则进行关闭
    AFTER_SECONDS: int = 600

    class Config:
        env_file = ".env"

    def get_logger(self):
        """
        设置日志
        """
        if self.LOGGER is None:
            logging_dict = get_logging_dict(self.LOG_LEVEL, self.BASE_DIR / self.LOG_DIR, self.PROJECT_NAME)
            logging.config.dictConfig(logging_dict)

            self.LOGGER = logging.getLogger('root')
            for handler in self.LOGGER.handlers:
                if handler.name == 'console':
                    fmt = logging_dict['formatters']['console']['format']
                    date_fmt = logging_dict['formatters']['console']['datefmt']
                    formatter = ColorFormatter(fmt=fmt, datefmt=date_fmt)
                    handler.setFormatter(formatter)
                    break

        return self.LOGGER
