from fastapi import FastAPI, applications, Request, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from watchtower.global_router import routers, tags_metadata
from watchtower.middleware.middlewares import middlewares
from watchtower.settings import settings, logger
from watchtower.status.types.exception import SiteException
from watchtower.status.types.response import Status


# ###################
# ###   定制界面   ###
# ##################
# 定制swagger界面元素
def get_swagger_ui_html_rewrite(*args, **kwargs):
    # 自定义元素
    if settings.SWAGGER_FAVICON_URL:
        kwargs["swagger_favicon_url"] = settings.SWAGGER_FAVICON_URL
    if settings.SWAGGER_JS_URL:
        kwargs["swagger_js_url"] = settings.SWAGGER_JS_URL
    if settings.SWAGGER_CSS_URL:
        kwargs["swagger_css_url"] = settings.SWAGGER_CSS_URL
    return get_swagger_ui_html(*args, **kwargs)


# 定制redoc界面元素
def get_redoc_html_rewrite(*args, **kwargs):
    # 自定义元素
    if settings.REDOC_FAVICON_RUL:
        kwargs["redoc_favicon_url"] = settings.REDOC_FAVICON_RUL
    if settings.REDOC_JS_RUL:
        kwargs["redoc_js_url"] = settings.REDOC_JS_RUL
    return get_redoc_html(*args, **kwargs)


applications.get_swagger_ui_html = get_swagger_ui_html_rewrite
applications.get_redoc_html = get_redoc_html_rewrite

if settings.ENV == "product":
    openapi_url = None
    docs_url = None
    redoc_url = None
else:
    openapi_url = settings.OPENAPI_URL
    docs_url = settings.DOCS_URL
    redoc_url = settings.REDOC_URL

app = FastAPI(
    title=settings.SITE_TITLE,
    description=settings.SITE_DESCRIPTION,
    version=settings.DOCS_VERSION,
    terms_of_service=settings.TERMS_OF_SERVICE,
    contact=settings.CONTACT,
    license_info=settings.LICENSE_INFO,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
)

# 导入全局中间件
for middleware in middlewares:
    app.add_middleware(**middleware)

# 导入路由信息
for router in routers:
    app.include_router(**router, prefix=settings.URL_PREFIX)

app.openapi_tags = tags_metadata


# 自定义openapi显示
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.SITE_TITLE,
        version=settings.DOCS_VERSION,
        openapi_version=app.openapi_version,
        description=settings.SITE_DESCRIPTION,
        routes=app.routes,
        terms_of_service=settings.TERMS_OF_SERVICE,
        contact=settings.CONTACT,
        license_info=settings.LICENSE_INFO,
        tags=app.openapi_tags,
        servers=app.servers,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# 自定义静态文件路径
if settings.STATIC_URL and settings.STATIC_PATH:
    app.mount(settings.STATIC_URL, StaticFiles(directory=settings.STATIC_PATH), name="static")

# 是否是一个需要数据库的项目
if settings.DB_ENABLE:
    from oracle.sqlalchemy import sql_helper

    sql_helper.init_orm()
    # DATABASE_URL = f"{settings.WRITE_ENGINE}://{settings.WRITE_USER}:{settings.WRITE_PASSWORD}@{settings.WRITE_HOST}:{settings.WRITE_PORT}/{settings.WRITE_DATABASE}"
    # sql_helper.register_sqlalchemy(app, DATABASE_URL, async_mode=True)


@app.exception_handler(SiteException)
async def unicorn_site_exception_handle(_: Request, exc: SiteException):
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(exc.response),
        headers=exc.headers
    )


@app.exception_handler(HTTPException)
async def unicorn_http_exception_handle(_: Request, exc: HTTPException):
    if isinstance(exc.detail, Status):
        exception_status = exc.detail.code
        exception_message = exc.detail.message
    else:
        exception_status = str(exc.status_code)
        exception_message = exc.detail
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder({
            "code": exception_status,
            "message": exception_message,
            "success": False,
            "data": {},
        }),
        headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.error(f"数据解析出错，错误原因为 {errors}")

    data = dict()
    message = ''
    if errors and isinstance(errors, list):
        data = errors[0]
        field = len(data['loc']) > 1 and data['loc'][1] or data['loc'][0]
        msg = data['msg']
        message = f"字段 {field} 不合法 => {msg}"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        # content=jsonable_encoder({"detail": exc.errors(), "Error": "Name field is missing"}),
        content=jsonable_encoder({
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": message,
            "success": False,
            "data": data,
        })
    )
