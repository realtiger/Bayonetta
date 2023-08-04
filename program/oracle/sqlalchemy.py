import re
import time
from datetime import datetime
from typing import Type, Any, Callable, Generator, Coroutine, Sequence, Optional

from fastapi import Depends, Query, Body
from pydantic import create_model
from sqlalchemy import select, func, Enum, DateTime, Select, desc, asc, delete, update, MetaData, BigInteger
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import DeclarativeMeta as Model
from sqlalchemy.orm import ColumnProperty, RelationshipProperty, DeclarativeBase, Mapped, mapped_column, selectinload

from oracle.crud_base import CRUDGenerator, get_pk_type
from oracle.snowflake import snow
from oracle.types import DEPENDENCIES, PYDANTIC_SCHEMA as SCHEMA, PAGINATION, ModelStatus, T, ITEM_NOT_FOUND_CODE, MULTIPLE_RESULTS_FOUND_CODE, PRIMARY_KEY_EXISTED_CODE, \
    CREATE_FAILED_CODE, UPDATE_FAILED_CODE, DELETE_FAILED_CODE
from watchtower import PayloadData, optional_signature_authentication, Response, SiteException
from watchtower.settings import logger, settings
from watchtower.status.global_status import StatusMap
from watchtower.status.types.response import GetAllData, PaginationData, generate_response_model, Status

Session = Callable[..., Generator[AsyncSession, Any, None]]

RESPONSE_CALLABLE = Callable[..., Coroutine[Any, Any, Response]]
RESPONSE_CALLABLE_LIST = Callable[..., Coroutine[Any, Any, Response[GetAllData]]]

ItemNotFound = generate_response_model("ItemNotFound", StatusMap.ITEM_NOT_FOUND)
MultipleResults = generate_response_model("MultipleResults", StatusMap.MULTIPLE_RESULTS_FOUND)
PrimaryKeyExisted = generate_response_model("PrimaryKeyExisted", StatusMap.PRIMARY_KEY_EXISTED)
CreateFailed = generate_response_model("CreateFailed", StatusMap.CREATE_FAILED)
UpdateFailed = generate_response_model("UpdateFailed", StatusMap.UPDATE_FAILED)
DeleteFailed = generate_response_model("DeleteFailed", StatusMap.DELETE_FAILED)

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
            delete_all_route: bool | DEPENDENCIES = True,
            get_all_route_params: dict | None = None,
            get_one_route_params: dict | None = None,
            create_route_params: dict | None = None,
            update_route_params: dict | None = None,
            delete_one_route_params: dict | None = None,
            delete_all_route_params: dict | None = None,
            verbose_name: str = '',
            verbose_name_plural: str = '',
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
            prefix=prefix or db_model.__tablename__,
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

            # TODO 权限判断，这里只是简单的判断是否有管理员字段
            # 现有阶段只判断"status:all"是否存在，后续可根据需求扩展
            # 生成token时，如果是超级用户，会主动将"status:all"加入scopes中
            # 如果是普通用户，只能查看status为active的数据
            if payload is None or "status:all" not in payload.scopes:
                filters_dict['status'] = ModelStatus.ACTIVE.value

            all_records, count_records, pagination = await self._orm_get_all(pagination, filters_dict, orders)

            pagination_data = PaginationData(index=pagination.index, limit=pagination.limit, total=count_records, offset=pagination.offset)
            data = GetAllData(items=all_records, pagination=pagination_data).dict()
            response = Response[GetAllData](data=data)

            return response

        return route

    def _create(self, *args: Any, **kwargs: Any) -> RESPONSE_CALLABLE:
        async def route(model: self.create_schema) -> Response[self.schema]:  # type: ignore
            async with self.db_func().begin() as session:
                try:
                    model_dict = self._create_validator(model.dict())

                    db_model_data = {}
                    for key in self.db_model.__table__.columns.keys():
                        if key in model_dict:
                            db_model_data[key] = model_dict[key]

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
            # 这里会把 Model 类型自动转换为 schema 类型
            # 直接使用 return Response[self.schema](data=db_model) 编辑器会发出警告，因此先赋值再返回
            response.update(data=db_model)
            return response

        return route

    def _delete_all(self, *args: Any, **kwargs: Any) -> RESPONSE_CALLABLE_LIST:
        async def route(
                item_ids: list[self._primary_key_type] = Body(default=None, title="id list", description="delete item's id list", example=[1, 2, 3])  # type: ignore
        ) -> Response[GetAllData]:  # type: ignore
            all_records, count, pagination = await self._orm_get_all_by_ids(item_ids)
            delete_statement = delete(self.db_model).filter(getattr(self.db_model, self._primary_key).in_(item_ids)).returning(self.db_model)

            async with self.db_func().begin() as session:
                await session.execute(delete_statement)
                await session.commit()

            if count > 0:
                pagination.limit = count
                pagination.total = count
            data = GetAllData(items=all_records, pagination=pagination).dict()
            return Response[GetAllData](data=data)

        return route

    def _get_one(self, *args: Any, **kwargs: Any) -> RESPONSE_CALLABLE:
        async def route(item_id: self._primary_key_type) -> Response[self.schema]:  # type: ignore
            model = await self._orm_get_one(item_id)

            response = Response[self.schema]()
            response.update(data=model)
            return response

        return route

    def _update(self, *args: Any, **kwargs: Any) -> RESPONSE_CALLABLE:
        async def route(item_id: self._primary_key_type, model: self.update_schema) -> Response[self.schema]:  # type: ignore
            # 只获取更新后的字段
            data = model.dict(exclude_unset=True, exclude={self._primary_key})
            update_statement = update(self.db_model).where(getattr(self.db_model, self._primary_key) == item_id).values(**data)

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

            db_model = await self._orm_get_one(item_id)
            data = self._format_query_data(db_model)

            response = Response[self.schema]()
            response.update(data=data)
            return response

        return route

    def _delete_one(self, *args, **kwargs) -> RESPONSE_CALLABLE:
        async def route(item_id: self._primary_key_type) -> Response[self.schema]:  # type: ignore
            result = await self._orm_get_one(item_id)
            data = self._format_query_data(result)
            delete_statement = delete(self.db_model).where(getattr(self.db_model, self._primary_key) == item_id).returning(self.db_model)

            async with self.db_func().begin() as session:
                try:
                    await session.execute(delete_statement)
                    await session.commit()
                except Exception as error:
                    await session.rollback()
                    logger.error(f"delete {self.db_model.__name__} error: {error}")
                    raise SiteException(status_code=DELETE_FAILED_CODE, response=Response[dict](status=StatusMap.DELETE_FAILED)) from None

            response = Response[self.schema]()
            response.update(data=data)
            return response

        return route

    async def _orm_get_all(self, pagination: PAGINATION = None, filters: dict[str, str] = None, orders: list[str] = None) -> tuple[Sequence, int, PAGINATION]:
        if pagination is None:
            pagination = self.pagination()
        if filters is None:
            filters = {}
        if orders is None:
            orders = [getattr(self.db_model, self._primary_key).name]

        orders_formatter = self._order_formatter(orders)

        all_statement, count_statement = self._orm_get_all_statement(pagination, filters, orders_formatter)

        async with self.db_func().begin() as session:
            all_records = list()
            # execute the statement
            all_records_data = (await session.execute(all_statement)).scalars().all()
            for row in all_records_data:
                all_records.append(self._format_query_data(row))
            count_records = (await session.execute(count_statement)).scalar()
        return all_records, count_records, pagination

    async def _orm_get_all_by_ids(self, ids: [int] = None, orders: list[str] = None) -> tuple[Sequence, int, PAGINATION]:
        if orders is None:
            orders = [getattr(self.db_model, self._primary_key).name]

        orders_formatter = self._order_formatter(orders)
        all_statement_by_ids = select(self.db_model).where(getattr(self.db_model, self._primary_key).in_(ids)).order_by(*orders_formatter)

        async with self.db_func().begin() as session:
            all_records = list()
            # execute the statement
            all_records_data = (await session.execute(all_statement_by_ids)).scalars().all()
            for row in all_records_data:
                all_records.append(self._format_query_data(row))
        return all_records, len(all_records), PAGINATION()

    async def _orm_get_one(self, item_id) -> Model:
        filter_params = {self._primary_key: item_id}
        statement = self._orm_get_one_statement(filter_params)
        async with self.db_func().begin() as session:
            try:
                model = await session.execute(statement)
                model = model.scalar_one()
            except MultipleResultsFound:
                response = Response[dict](status=StatusMap.MULTIPLE_RESULTS_FOUND, data={"message": "Multiple results found"})
                raise SiteException(status_code=MULTIPLE_RESULTS_FOUND_CODE, response=response) from None
            except NoResultFound:
                response = Response[dict](status=StatusMap.ITEM_NOT_FOUND, data={"message": "Item not found"})
                raise SiteException(status_code=ITEM_NOT_FOUND_CODE, response=response) from None
        return model

    def _orm_get_all_statement(self, pagination: PAGINATION, filters: dict[str, str], orders: list) -> tuple[Select, Select]:
        # query count statement
        count_statement = select(func.count()).select_from(self.db_model).filter_by(**filters)
        _, foreign_key_columns = self._get_columns()

        # query all statement
        # all_statement = select(*columns).select_from(self.db_model).filter_by(**filters).order_by(*orders).offset(pagination.offset).limit(pagination.limit)
        all_statement = select(self.db_model).filter_by(**filters).order_by(*orders).offset(pagination.offset).limit(pagination.limit)

        for column in foreign_key_columns:
            all_statement = all_statement.join(column, isouter=True).options(selectinload(column))

        # all_statement = all_statement.filter_by(**filters).order_by(*orders).offset(pagination.offset).limit(pagination.limit)

        return all_statement, count_statement

    def _orm_get_one_statement(self, filters: dict[str, str]) -> Select:
        _, foreign_key_columns = self._get_columns()
        statement = select(self.db_model).filter_by(**filters)

        for column in foreign_key_columns:
            statement = statement.join(column, isouter=True).options(selectinload(column))

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

    def _format_query_data(self, row) -> dict:
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
                row_dict[field.key] = [child.id for child in getattr(row, field.key)]

        return row_dict

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
            add_delete_fail: bool = False
    ) -> tuple[str, str, dict, Any]:
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

        return params.get('summary', summary), params.get('description', description), responses, params.get('response_model')

    def _order_formatter(self, orders: [str]) -> list:
        orders_formatter = []
        for order in orders:
            field, order_func = (order[1:], desc) if order.startswith('-') else (order, asc)

            if not hasattr(self.db_model, field):
                continue

            orders_formatter.append(order_func(getattr(self.db_model, field)))

        return orders_formatter

    def _create_validator(self, item: dict) -> dict:
        """
        校验创建数据， 返回校验后的数据
        :param item:
        :return:
        """
        return item
