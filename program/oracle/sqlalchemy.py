import re
import time
from datetime import datetime
from typing import Type, Any, Callable, Generator, Coroutine, Sequence, Optional, Iterable

from fastapi import Depends, Query, Body, Request
from fastapi.types import DecoratedCallable
from pydantic import create_model
from sqlalchemy import select, func, Enum, DateTime, Select, desc, asc, delete, update, MetaData, BigInteger, Update
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import DeclarativeMeta as Model
from sqlalchemy.orm import ColumnProperty, RelationshipProperty, DeclarativeBase, Mapped, mapped_column, selectinload

from oracle.crud_base import CRUDGenerator, get_pk_type
from oracle.snowflake import snow
from oracle.types import DEPENDENCIES, PYDANTIC_SCHEMA as SCHEMA, PAGINATION, ModelStatus, T, ITEM_NOT_FOUND_CODE, MULTIPLE_RESULTS_FOUND_CODE, PRIMARY_KEY_EXISTED_CODE, \
    CREATE_FAILED_CODE, UPDATE_FAILED_CODE, DELETE_FAILED_CODE, ONLY_SUPERUSER_CODE
from oracle.utils import is_superuser
from watchtower import PayloadData, optional_signature_authentication, Response, SiteException
from watchtower.settings import logger, settings
from watchtower.status.global_status import StatusMap
from watchtower.status.types.response import GetAllData, PaginationData, generate_response_model, Status

Session = Callable[..., Generator[AsyncSession, Any, None]]

RESPONSE_CALLABLE = Callable[..., Coroutine[Any, Any, Response]]
RESPONSE_CALLABLE_LIST = Callable[..., Coroutine[Any, Any, Response[GetAllData]]]

OnlySuper = generate_response_model("OnlySuperuser", StatusMap.ONLY_SUPERUSER)
ItemNotFound = generate_response_model("ItemNotFound", StatusMap.ITEM_NOT_FOUND)
MultipleResults = generate_response_model("MultipleResults", StatusMap.MULTIPLE_RESULTS_FOUND)
PrimaryKeyExisted = generate_response_model("PrimaryKeyExisted", StatusMap.PRIMARY_KEY_EXISTED)
CreateFailed = generate_response_model("CreateFailed", StatusMap.CREATE_FAILED)
UpdateFailed = generate_response_model("UpdateFailed", StatusMap.UPDATE_FAILED)
DeleteFailed = generate_response_model("DeleteFailed", StatusMap.DELETE_FAILED)

# 为其他请求预留响应模式
ONLY_SUPERUSER_RESPONSE = {
    ONLY_SUPERUSER_CODE: {
        "model": OnlySuper,
        "description": "只有超级用户才能访问",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.ONLY_SUPERUSER.code,
                    "success": StatusMap.ONLY_SUPERUSER.success,
                    "message": StatusMap.ONLY_SUPERUSER.message,
                    "data": {}
                }
            }
        }
    }
}

ITEM_NOT_FOUND_RESPONSE = {
    ITEM_NOT_FOUND_CODE: {
        "model": ItemNotFound,
        "description": "数据不存在",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.ITEM_NOT_FOUND.code,
                    "success": StatusMap.ITEM_NOT_FOUND.success,
                    "message": StatusMap.ITEM_NOT_FOUND.message,
                    "data": {}
                }
            }
        }
    }
}

MULTIPLE_RESULTS_FOUND_RESPONSE = {
    MULTIPLE_RESULTS_FOUND_CODE: {
        "model": MultipleResults,
        "description": "找到多条数据",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.MULTIPLE_RESULTS_FOUND.code,
                    "success": StatusMap.MULTIPLE_RESULTS_FOUND.success,
                    "message": StatusMap.MULTIPLE_RESULTS_FOUND.message,
                    "data": {}
                }
            }
        }
    }
}

PRIMARY_KEY_EXISTED_RESPONSE = {
    PRIMARY_KEY_EXISTED_CODE: {
        "model": PrimaryKeyExisted,
        "description": "唯一数据已存在",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.PRIMARY_KEY_EXISTED.code,
                    "success": StatusMap.PRIMARY_KEY_EXISTED.success,
                    "message": StatusMap.PRIMARY_KEY_EXISTED.message,
                    "data": {}
                }
            }
        }
    }
}

CREATE_FAILED_RESPONSE = {
    CREATE_FAILED_CODE: {
        "model": CreateFailed,
        "description": "创建失败",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.CREATE_FAILED.code,
                    "success": StatusMap.CREATE_FAILED.success,
                    "message": StatusMap.CREATE_FAILED.message,
                    "data": {}
                }
            }
        }
    }
}

UPDATE_FAILED_RESPONSE = {
    UPDATE_FAILED_CODE: {
        "model": UpdateFailed,
        "description": "更新失败",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.UPDATE_FAILED.code,
                    "success": StatusMap.UPDATE_FAILED.success,
                    "message": StatusMap.UPDATE_FAILED.message,
                    "data": {}
                }
            }
        }
    }
}

DELETE_FAILED_RESPONSE = {
    DELETE_FAILED_CODE: {
        "model": DeleteFailed,
        "description": "删除失败",
        "content": {
            "application/json": {
                "example": {
                    "code": StatusMap.DELETE_FAILED.code,
                    "success": StatusMap.DELETE_FAILED.success,
                    "message": StatusMap.DELETE_FAILED.message,
                    "data": {}
                }
            }
        }
    }
}


class ValidationError(Exception):
    pass


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": 'ix_@_%(column_0_label)s',
        "uq": "uq_@_%(table_name)s_@_%(column_0_name)s",
        "ck": "ck_@_%(table_name)s_@_%(constraint_name)s",
        "fk": "fk_@_%(table_name)s_@_%(column_0_name)s_@_%(referred_table_name)s",
        # "pk": "pk_@_%(table_name)s"
    })


class SqlHelper:
    engine = None
    session: async_sessionmaker | None = None
    model_base = Base

    def init_orm(self) -> None:
        db_url = f"{settings.DB_ENGINE}://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_DATABASE}"
        self.engine = create_async_engine(db_url, future=True, echo=settings.DB_ECHO, pool_pre_ping=True, pool_recycle=3600)
        self.session = async_sessionmaker(self.engine, expire_on_commit=False)

    def get_session(self) -> async_sessionmaker | None:
        return self.session


sql_helper = SqlHelper()

ModelBase = sql_helper.model_base


class SiteBaseModel(ModelBase):
    __abstract__ = True

    id: Mapped[int] = mapped_column("id", BigInteger, primary_key=True, default=snow.get_id, comment="索引")
    # 如果是postgres数据库，需要先手动创建enum类型
    # CREATE TYPE ModelStatus AS ENUM ('active', 'inactive', 'frozen', 'obsolete');
    status: Mapped[ModelStatus] = mapped_column("status", Enum(ModelStatus), default=ModelStatus.ACTIVE, comment="数据状态")
    level: Mapped[int] = mapped_column("level", BigInteger, default=lambda: int(time.time() * 1000 - 1673366400000), comment="等级")
    create_time: Mapped[datetime] = mapped_column("create_time", DateTime, default=datetime.now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column("update_time", DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")


class SQLAlchemyCRUDRouter(CRUDGenerator[SCHEMA]):
    def __init__(
            self,
            schema: Type[SCHEMA],
            db_model: Type[Model],
            # db: Session,
            create_schema: Type[SCHEMA] | None = None,
            update_schema: Type[SCHEMA] | None = None,
            prefix: str | None = None,
            tags: list[str] | None = None,
            paginate: int | None = None,
            get_all_route: bool | DEPENDENCIES = True,
            get_one_route: bool | DEPENDENCIES = True,
            create_route: bool | DEPENDENCIES = True,
            update_route: bool | DEPENDENCIES = True,
            delete_one_route: bool | DEPENDENCIES = True,
            delete_all_route: bool | DEPENDENCIES = False,
            get_all_route_params: dict | None = None,
            get_one_route_params: dict | None = None,
            create_route_params: dict | None = None,
            update_route_params: dict | None = None,
            delete_one_route_params: dict | None = None,
            delete_all_route_params: dict | None = None,
            verbose_name: str = '',
            verbose_name_plural: str = '',
            delete_update_field: str = '',
            **kwargs: Any
    ) -> None:
        self.db_model = db_model
        self.db_func = sql_helper.get_session
        self._primary_key: str = db_model.__table__.primary_key.columns.keys()[0]
        self._primary_key_type: type = get_pk_type(schema, self._primary_key)

        if verbose_name:
            self.verbose_name = verbose_name
        else:
            self.verbose_name = schema.__name__.capitalize()
        if self.verbose_name and not verbose_name_plural:
            self.verbose_name_plural = f"{self.verbose_name}s"
        else:
            self.verbose_name_plural = verbose_name_plural

        self.delete_update_field = delete_update_field

        if not isinstance(get_all_route_params, dict):
            get_all_route_params = {}
        get_all_route_params.setdefault("summary", f'Get All {self.verbose_name_plural}')
        if get_all_route_params.get("response_model") is None:
            get_all_route_params["response_model"] = create_model(
                f'{self.verbose_name.title()}GetAllDataResponse', items=(Optional[list[schema]], ...), pagination=(PaginationData, ...)
            )

        if not isinstance(get_one_route_params, dict):
            get_one_route_params = {}
        get_one_route_params.setdefault("summary", f'Get One {self.verbose_name}')

        if not isinstance(create_route_params, dict):
            create_route_params = {}
        create_route_params.setdefault("summary", f'Create One {self.verbose_name}')

        if not isinstance(update_route_params, dict):
            update_route_params = {}
        update_route_params.setdefault("summary", f'Update One {self.verbose_name}')

        if not isinstance(delete_one_route_params, dict):
            delete_one_route_params = {}
        delete_one_route_params.setdefault("summary", f'Delete One {self.verbose_name}')

        if not isinstance(delete_all_route_params, dict):
            delete_all_route_params = {}
        delete_all_route_params.setdefault("summary", f'Delete All {self.verbose_name_plural}')

        super().__init__(
            schema=schema,
            create_schema=create_schema,
            update_schema=update_schema,
            prefix=prefix or db_model.__tablename__.replace("_", "-"),
            tags=tags,
            paginate=paginate,
            get_all_route=get_all_route,
            get_one_route=get_one_route,
            create_route=create_route,
            update_route=update_route,
            delete_one_route=delete_one_route,
            delete_all_route=delete_all_route,
            get_all_route_params=get_all_route_params,
            get_one_route_params=get_one_route_params,
            create_route_params=create_route_params,
            update_route_params=update_route_params,
            delete_one_route_params=delete_one_route_params,
            delete_all_route_params=delete_all_route_params,
            **kwargs
        )

    # ##### 操作路由 #####
    def _add_api_route(
            self,
            path: str,
            endpoint: Callable[..., Any],
            dependencies: bool | DEPENDENCIES,
            methods: set[str] | list[str] | None = None,
            response_model: Sequence[Type[T]] | Type[T] | None = None,
            summary: str | None = None,
            description: str | None = None,
            responses: dict[int, dict[str, Any]] | None = None,
            **kwargs: Any
    ):
        response_model = Response[response_model]

        super()._add_api_route(path, endpoint, dependencies, methods, response_model, summary, description, responses, **kwargs)

    def api_route(
            self,
            path: str,
            methods: list[str] = None,
            response_model: Sequence[Type[T]] | Type[T] | None = None,
            *args,
            **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        response_model = Response[response_model]
        return super().api_route(path, methods, response_model=response_model, *args, **kwargs)

    # ##### 操作数据库 #####
    def _get_all(self, *args: Any, **kwargs: Any) -> RESPONSE_CALLABLE_LIST:
        async def route(
                pagination: PAGINATION = Depends(self.pagination),
                filters: list[str] = Query(
                    default=[],
                    title="filter params",
                    description="filter field and value",
                    example=["id=0"]
                ),
                orders: list[str] = Query(
                    default=[],
                    title="order params",
                    description="order field, if reverse add prefix '-' as '-id'",
                    example=["-id", "status"]
                ),
                ids: list[int] = Query(
                    default=[],
                    title="id params",
                    description="id list",
                    example=[1, 2, 3]
                ),
                payload: PayloadData | None = Depends(optional_signature_authentication)
        ) -> Response[GetAllData]:
            filters_dict = {}
            for f in filters:
                # 确保只有key和value
                if f.count("=") != 1:
                    continue
                # 将空格全部进行替换，然后再进行分割
                f = f.replace(" ", "").split("=")
                filters_dict[f[0]] = f[1]
            if not orders:
                orders = [getattr(self.db_model, self._primary_key).name]

            all_records, count_records, pagination = await self._orm_get_all(pagination, filters_dict, orders, ids, payload)

            pagination_data = PaginationData(index=pagination.index, limit=pagination.limit, total=count_records, offset=pagination.offset)
            data = GetAllData(items=all_records, pagination=pagination_data).dict()
            response = Response[GetAllData](data=data)

            return response

        return route

    def _create(self, *args: Any, **kwargs: Any) -> RESPONSE_CALLABLE:
        async def route(
                request: Request,
                model: self.create_schema,  # type: ignore
                payload: PayloadData | None = Depends(optional_signature_authentication)
        ) -> Response[self.schema]:  # type: ignore
            async with self.db_func().begin() as session:
                try:
                    model = await self._pre_create(model, request=request, payload=payload)
                    model_dict = await self._create_validator(model.dict())

                    db_model_data = {}
                    for key in self.db_model.__table__.columns.keys():
                        if key in model_dict:
                            db_model_data[key] = model_dict[key]

                    invalid, main_key, main_value = await self.is_main_field_value_invalid(db_model_data)

                    if invalid:
                        raise ValidationError(f"字段{main_key}的值{main_value}不允许以{await self.get_delete_prefix()}结尾")

                    db_model: Model = self.db_model(**db_model_data)
                    session.add(db_model)
                    await session.flush()
                    await session.commit()
                except IntegrityError as error:
                    await session.rollback()
                    # result = re.match(r'.*Duplicate entry (.*) for key.*', error.args[0])
                    result = re.match(r".*Duplicate entry '(.*)' for key '(.*)'.*", error.args[0])
                    if result:
                        key = "_".join(result.group(2).split("_@_")[2:])
                        value = result.group(1)
                        response = Response[dict](status=Status(StatusMap.PRIMARY_KEY_EXISTED.code, f"字段{key}的值{value}已存在"))
                        raise SiteException(status_code=PRIMARY_KEY_EXISTED_CODE, response=response) from None
                    response = Response[dict](status=StatusMap.PRIMARY_KEY_EXISTED)
                    raise SiteException(status_code=PRIMARY_KEY_EXISTED_CODE, response=response) from None
                except ValidationError as error:
                    validation_error_status = Status(StatusMap.DATA_VALIDATION_FAILED.code, error.args[0])
                    response = Response[dict](status=validation_error_status)
                    raise SiteException(status_code=CREATE_FAILED_CODE, response=response) from None
                except Exception as error:
                    await session.rollback()
                    logger.error(f"create {self.db_model.__name__} error: {error}")
                    response = Response[dict](status=StatusMap.CREATE_FAILED)
                    raise SiteException(status_code=CREATE_FAILED_CODE, response=response) from None
            response = Response[self.schema]()
            model = await self._orm_get_one(db_model.id, payload)

            data = await self._post_create(await self.format_query_data(model), request=request, payload=payload)
            response.update(data=data)
            return response

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> RESPONSE_CALLABLE_LIST:
        async def route(
                item_ids: list[self._primary_key_type] = Body(default=None, title="id list", description="delete item's id list", example=[1, 2, 3], ),  # type: ignore
                payload: PayloadData | None = Depends(optional_signature_authentication)
        ) -> Response[GetAllData]:  # type: ignore
            all_records, count, pagination = await self._orm_get_all_by_ids(item_ids, payload=payload)

            # 如果是真删除，则直接删除，否则将名称添加后缀 {时间戳[-6:]}_delete 并将 status 设置为 inactive
            # TODO 没有考虑超过数据库字符数量限制的情况
            if settings.REAL_DELETE:
                delete_statement = delete(self.db_model).filter(getattr(self.db_model, self._primary_key).in_(item_ids)).returning(self.db_model)

                async with self.db_func().begin() as session:
                    await session.execute(delete_statement)
                    await session.commit()
            else:
                async with self.db_func().begin() as session:
                    values = {'status': ModelStatus.OBSOLETE}
                    for row in all_records:
                        await self.set_delete_show_name(row, values)
                        delete_statement = update(self.db_model).where(getattr(self.db_model, self._primary_key) == row[self._primary_key]).values(**values)
                        await session.execute(delete_statement)

                    await session.commit()

            if count > 0:
                pagination.limit = count
                pagination.total = count
            data = GetAllData(items=all_records, pagination=pagination).dict()
            return Response[GetAllData](data=data)

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> RESPONSE_CALLABLE:
        async def route(item_id: self._primary_key_type, payload: PayloadData | None = Depends(optional_signature_authentication)) -> Response[self.schema]:  # type: ignore
            model = await self._orm_get_one(item_id, payload)

            response = Response[self.schema]()
            response.update(data=model)
            return response

        return route

    def _update(self, *args: Any, **kwargs: Any) -> RESPONSE_CALLABLE:
        async def route(
                request: Request,
                item_id: self._primary_key_type,  # type: ignore
                model: self.update_schema,  # type: ignore
                payload: PayloadData | None = Depends(optional_signature_authentication)
        ) -> Response[self.schema]:  # type: ignore
            # 只获取更新后的字段
            model = model.dict(exclude_unset=True, exclude={self._primary_key})
            model = await self._pre_update(model, request=request, payload=payload)

            invalid, main_key, main_value = await self.is_main_field_value_invalid(model)

            if invalid:
                raise SiteException(
                    status_code=UPDATE_FAILED_CODE,
                    response=Response[dict](status=Status(StatusMap.UPDATE_FAILED.code, f"字段{main_key}的值{main_value}不允许以_delete结尾"))
                ) from None

            # 保存原数据，为进一步操作做准备
            original_data = await self._orm_get_one(item_id, payload)

            update_statement = await self._orm_update_statement(item_id, model, payload)
            if update_statement is not None:
                async with self.db_func().begin() as session:
                    try:
                        await session.execute(update_statement)
                        await session.commit()
                    except Exception as error:
                        await session.rollback()
                        result = re.match(r".*Duplicate entry '(.*)' for key '(.*)'.*", error.args[0])
                        if result:
                            key = "".join(result.group(2).split("_@_")[2:])
                            value = result.group(1)
                            response = Response[dict](status=Status(StatusMap.PRIMARY_KEY_EXISTED.code, f"字段{key}的值{value}已存在"))
                            raise SiteException(status_code=PRIMARY_KEY_EXISTED_CODE, response=response) from None
                        logger.error(f"update {self.db_model.__name__} error: {error}")
                        raise SiteException(status_code=UPDATE_FAILED_CODE, response=Response[dict](status=StatusMap.UPDATE_FAILED)) from None

            db_model = await self._orm_get_one(item_id, payload)
            data = await self.format_query_data(db_model)

            data = await self._post_update(data, await self.format_query_data(original_data), request=request, payload=payload)
            response = Response[self.schema]()
            response.update(data=data)
            return response

        return route

    def _delete_one(self, *args, **kwargs) -> RESPONSE_CALLABLE:
        async def route(
                request: Request,
                item_id: self._primary_key_type,  # type: ignore
                payload: PayloadData | None = Depends(optional_signature_authentication)
        ) -> Response[self.schema]:  # type: ignore
            result = await self._orm_get_one(item_id, payload)
            data = await self.format_query_data(result)
            data = await self._pre_delete(data, request=request, payload=payload)

            # 如果是真删除，则直接删除，否则将名称添加后缀 _delete 并将 status 设置为 inactive
            if settings.REAL_DELETE:
                delete_statement = delete(self.db_model).where(getattr(self.db_model, self._primary_key) == item_id).returning(self.db_model)
            else:
                values = {'status': ModelStatus.OBSOLETE}
                await self.set_delete_show_name(data, values)
                delete_statement = update(self.db_model).where(getattr(self.db_model, self._primary_key) == item_id).values(**values)

            async with self.db_func().begin() as session:
                try:
                    await session.execute(delete_statement)
                    await session.commit()
                except Exception as error:
                    await session.rollback()
                    logger.error(f"delete {self.db_model.__name__} error: {error}")
                    raise SiteException(status_code=DELETE_FAILED_CODE, response=Response[dict](status=StatusMap.DELETE_FAILED)) from None

            data = await self._post_delete(data, request=request, payload=payload)
            response = Response[self.schema]()
            response.update(data=data)
            return response

        return route

    async def _orm_get_all(
            self,
            pagination: PAGINATION = None,
            filters: dict[str, str] = None,
            orders: list[str] = None,
            ids: list[int] = None,
            payload: PayloadData | None = None
    ) -> tuple[Sequence, int, PAGINATION]:
        if pagination is None:
            pagination = self.pagination()
        if filters is None:
            filters = {}
        if orders is None:
            orders = [getattr(self.db_model, self._primary_key).name]

        orders_formatter = self._order_formatter(orders)

        all_statement, count_statement = await self._orm_get_all_statement(pagination, filters, orders_formatter, ids, payload)

        async with self.db_func().begin() as session:
            all_records = list()
            # execute the statement
            all_records_data = (await session.execute(all_statement)).scalars().all()
            for row in all_records_data:
                all_records.append(await self.format_query_data(row))
            count_records = (await session.execute(count_statement)).scalar()
        return all_records, count_records, pagination

    async def _orm_get_all_by_ids(self, ids: [int] = None, orders: list[str] = None, payload: PayloadData | None = None) -> tuple[Sequence, int, PAGINATION]:
        if orders is None:
            orders = [getattr(self.db_model, self._primary_key).name]

        # 普通用户只能查看 active 状态的数据
        status_list = [ModelStatus.ACTIVE.value]
        # 超级用户可以查看所有状态的数据
        if await is_superuser(payload):
            status_list.extend([ModelStatus.INACTIVE.value, ModelStatus.FROZEN.value])

        orders_formatter = self._order_formatter(orders)
        all_statement_by_ids = select(self.db_model).where(
            getattr(self.db_model, self._primary_key).in_(ids),
            getattr(self.db_model, 'status').in_(status_list)
        ).order_by(*orders_formatter)

        async with self.db_func().begin() as session:
            all_records = list()
            # execute the statement
            all_records_data = (await session.execute(all_statement_by_ids)).scalars().all()
            for row in all_records_data:
                all_records.append(await self.format_query_data(row))
        return all_records, len(all_records), PAGINATION()

    async def _orm_get_one(self, item_id, payload: PayloadData | None) -> Model:
        filter_params = {self._primary_key: item_id}
        statement = await self._orm_get_one_statement(filter_params, payload)
        async with self.db_func().begin() as session:
            try:
                model = await session.execute(statement)
                model = model.scalar_one()
            except MultipleResultsFound:
                response = Response[dict](status=StatusMap.MULTIPLE_RESULTS_FOUND)
                raise SiteException(status_code=MULTIPLE_RESULTS_FOUND_CODE, response=response) from None
            except NoResultFound:
                response = Response[dict](status=StatusMap.ITEM_NOT_FOUND)
                raise SiteException(status_code=ITEM_NOT_FOUND_CODE, response=response) from None
        return model

    async def _orm_get_all_statement(
            self,
            pagination: PAGINATION,
            filters: dict[str, str | list],
            orders: list, ids: list[int],
            payload: PayloadData | None
    ) -> tuple[Select, Select]:
        _, foreign_key_columns = self._get_columns()
        filter_value = await self.format_select_filter_params(filters, payload)

        # query count statement
        count_statement = select(func.count()).select_from(self.db_model).filter(*filter_value).distinct()
        # query all statement
        all_statement = select(self.db_model).filter(*filter_value).order_by(*orders).offset(pagination.offset).limit(pagination.limit).distinct()

        if ids:
            all_statement = all_statement.where(getattr(self.db_model, self._primary_key).in_(ids))

        for column in foreign_key_columns:
            all_statement = all_statement.join(column, isouter=True).options(selectinload(column))

        return all_statement, count_statement

    async def _orm_get_one_statement(self, filters: dict[str, str | list], payload: PayloadData | None) -> Select:
        _, foreign_key_columns = self._get_columns()

        filter_value = await self.format_select_filter_params(filters, payload)
        statement = select(self.db_model).filter(*filter_value)

        for column in foreign_key_columns:
            statement = statement.join(column, isouter=True).options(selectinload(column)).distinct()

        return statement

    async def _orm_update_statement(self, item_id: int, data: dict, payload: PayloadData | None = None) -> Update | None:
        if not data:
            return

        statement = update(self.db_model).where(getattr(self.db_model, self._primary_key) == item_id).values(**data)
        return statement

    def _get_columns(self) -> tuple[list, list]:
        common_columns = []
        foreign_key_columns = []
        for field in self.schema.__fields__.keys():
            if hasattr(self.db_model, field):
                db_model_field = getattr(self.db_model, field)
                if isinstance(db_model_field.property, ColumnProperty):
                    common_columns.append(db_model_field)
                elif isinstance(db_model_field.property, RelationshipProperty):
                    foreign_key_columns.append(db_model_field)
        return common_columns, foreign_key_columns

    async def format_query_data(self, row) -> dict:
        """
        格式化查询数据，单条数据格式化
        :param row: 每一行数据
        :return:
        """
        column, foreign_key_columns = self._get_columns()
        # 整理数据
        row_dict = dict()
        for field in column:
            if hasattr(row, field.key):
                row_dict[field.key] = getattr(row, field.key)
        for field in foreign_key_columns:
            if hasattr(row, field.key):
                foreign_value = getattr(row, field.key)
                if foreign_value is None:
                    row_dict[field.key] = 0
                else:
                    value = getattr(row, field.key)
                    if isinstance(value, Iterable):
                        row_dict[field.key] = [child.id for child in getattr(row, field.key)]
                    else:
                        row_dict[field.key] = value

        return row_dict

    async def is_main_field_value_invalid(self, model: dict) -> tuple[bool, str, str]:
        """
        检查主要字段的值是否不合法
        :param model:
        :return:
        """
        main_columns_key = ''
        main_columns_value = ''
        if 'name' in model:
            main_columns_key = 'name'
            main_columns_value = model['name']
        elif 'title' in model:
            main_columns_key = 'title'
            main_columns_value = model['title']
        elif self.delete_update_field and self.delete_update_field in model:
            main_columns_key = self.delete_update_field
            main_columns_value = model[self.delete_update_field]

        return main_columns_value.endswith(await self.get_delete_prefix()), main_columns_key, main_columns_value

    @staticmethod
    def format_params(
            summary: str,
            description: str,
            params: dict | None = None,
            responses: dict | None = None,
            add_404: bool = False,
            add_key_exist: bool = False,
            add_create_fail: bool = False,
            add_update_fail: bool = False,
            add_delete_fail: bool = False,
            return_type: str = None
    ) -> tuple[str, str, dict, Any] | dict[str, Any]:
        if not isinstance(params, dict):
            params = {}

        responses = params.get('responses', responses)
        if not isinstance(responses, dict):
            responses = {}

        if add_404:
            responses.update(ITEM_NOT_FOUND_RESPONSE)
            responses.update(MULTIPLE_RESULTS_FOUND_RESPONSE)

        if add_key_exist:
            responses.update(PRIMARY_KEY_EXISTED_RESPONSE)

        if add_create_fail:
            responses.update(CREATE_FAILED_RESPONSE)

        if add_update_fail:
            responses.update(UPDATE_FAILED_RESPONSE)

        if add_delete_fail:
            responses.update(DELETE_FAILED_RESPONSE)

        if return_type == 'dict':
            return {
                'summary': params.get('summary', summary),
                'description': params.get('description', description),
                'responses': responses,
                'response_model': params.get('response_model')
            }
        return params.get('summary', summary), params.get('description', description), responses, params.get('response_model')

    def _order_formatter(self, orders: [str]) -> list:
        orders_formatter = []
        for order in orders:
            field, order_func = (order[1:], desc) if order.startswith('-') else (order, asc)

            if not hasattr(self.db_model, field):
                continue

            orders_formatter.append(order_func(getattr(self.db_model, field)))

        return orders_formatter

    async def _create_validator(self, item: dict) -> dict:
        """
        校验创建数据， 返回校验后的数据
        :param item:
        :return:
        """
        return item

    async def _pre_get_all(
            self,
            pagination: PAGINATION,
            filters: dict[str, str],
            orders: list[str], ids: list[int],
            payload: PayloadData | None
    ) -> tuple[PAGINATION, dict[str, str], list[str], list[int]]:
        """
        获取所有数据前的操作，返回操作后的数据
        :param pagination:
        :param filters:
        :param orders:
        :param ids:
        :return:
        """
        return pagination, filters, orders, ids

    async def _post_get_all(
            self,
            all_records: Sequence,
            count_records: int,
            pagination: PaginationData,
            payload: PayloadData | None
    ) -> tuple[Sequence, int, PaginationData]:
        """
        获取所有数据后的操作，返回操作后的数据
        :param all_records:
        :param count_records:
        :param pagination:
        :return:
        """
        return all_records, count_records, pagination

    async def _pre_create(self, item, request: Request | None = None, payload: PayloadData | None = None):
        """
        创建数据前的操作，返回操作后的数据
        :param item:
        :return:
        """
        return item

    async def _post_create(self, item: dict, request: Request | None = None, payload: PayloadData | None = None) -> dict:
        """
        创建数据后的操作，返回操作后的数据
        :param item:
        :return:
        """
        return item

    async def _pre_update(self, item: dict, request: Request | None = None, payload: PayloadData | None = None) -> dict:
        """
        更新数据前的操作，返回操作后的数据
        :param item:
        :return:
        """
        return item

    async def _post_update(self, item: dict, original_data: dict, request: Request | None = None, payload: PayloadData | None = None) -> dict:
        """
        更新数据后的操作，返回操作后的数据
        :param item:
        :return:
        """
        return item

    async def _pre_delete(self, item: dict, request: Request | None = None, payload: PayloadData | None = None) -> dict:
        """
        删除数据前的操作，返回操作后的数据
        :param item:
        :return:
        """
        return item

    async def _post_delete(self, item: dict, request: Request | None = None, payload: PayloadData | None = None) -> dict:
        """
        删除数据后的操作，返回操作后的数据
        :param item:
        :return:
        """
        return item

    async def format_select_filter_params(self, filters: dict[str, str | list], payload: PayloadData | None) -> list:
        """
        格式化查询参数
        :param filters:
        :return:
        """
        status_list = [ModelStatus.ACTIVE.value, ModelStatus.INACTIVE.value, ModelStatus.FROZEN.value]
        # 只有超级用户可以查看所有状态的数据，其他用户不能看到逻辑删除的数据
        if 'status' in filters:
            # 含有 status 筛选条件并且不是超级用户，则需要筛除逻辑删除的数据
            if not await is_superuser(payload):
                if isinstance(filters['status'], list) and ModelStatus.OBSOLETE.value in filters['status']:
                    filters['status'].remove(ModelStatus.OBSOLETE.value)
                elif isinstance(filters['status'], str) and filters['status'] == ModelStatus.OBSOLETE.value:
                    # 保证查询不到任何数据
                    filters['status'] = 'unknown'
            # 是超级用户则全部放行即可
            # else:
            #     pass
        else:
            # 没有 status 筛选条件则默认只查询 active 状态的数据
            filters['status'] = status_list

        filter_value = list()
        for key in filters:
            if isinstance(filters[key], list):
                filter_value.append(getattr(self.db_model, key).in_(filters[key]))
            else:
                filter_value.append(getattr(self.db_model, key) == filters[key])

        return filter_value

    async def get_delete_prefix(self):
        return "(deleted)"

    async def set_delete_show_name(self, row, values):
        # 6位时间戳后缀，最小限度保证唯一性
        timestamp_last_six = str(int(time.time()))[-6:]
        prefix = f"{timestamp_last_six}{await self.get_delete_prefix()}"
        if 'name' in row:
            values['name'] = f"{row['name']}_{prefix}"
        elif 'title' in row:
            values['title'] = f"{row['title']}_{prefix}"
        elif self.delete_update_field and self.delete_update_field in row:
            values[self.delete_update_field] = f"{row[self.delete_update_field]}_{prefix}"
