from abc import abstractmethod, ABC
from typing import Callable, Generic, Type, Any, Sequence

from fastapi import APIRouter, HTTPException, Depends
from fastapi.types import DecoratedCallable
from pydantic import create_model
from pydantic.generics import GenericModel

from oracle.types import T, DEPENDENCIES, PAGINATION, PYDANTIC_SCHEMA


def get_pk_type(schema: Type[PYDANTIC_SCHEMA], pk_field: str) -> type:
    try:
        return schema.__fields__[pk_field].type_
    except ValueError | KeyError:
        return int


def schema_factory(schema_cls: Type[T], pk_field_name: str = 'id', name: str = 'Create') -> Type[T]:
    """
    Is used to create a CreateSchema which does not contain pk
    """

    fields = {f.name: (f.type_, ...) for f in schema_cls.__fields__.values() if f.name != pk_field_name}

    name = f'{schema_cls.__name__}{name}'
    schema: Type[T] = create_model(__model_name=name, **fields)
    return schema


def create_query_validation_exception(field: str, msg: str) -> HTTPException:
    return HTTPException(
        422,
        detail={
            "detail": [{
                "loc": ["query", field],
                "msg": f"error: {msg}",
                "type": "type_error.integer"
            }]
        }
    )


def pagination_factory(max_limit: int | None = None) -> Depends:
    """
    Created the pagination dependency to be used in the router
    """

    if max_limit is None:
        max_limit = 50

    def pagination(index: int = 1, limit: int = max_limit) -> PAGINATION:
        """
        分页结构
        :param index: 当前页码
        :param limit: 每页多少数据
        :return:
        """
        if index < 1:
            raise create_query_validation_exception("skip", "index query parameter must be greater zero")

        if limit is not None:
            if limit <= 0:
                raise create_query_validation_exception("limit", "limit query parameter must be greater then zero")
            elif max_limit and max_limit < limit:
                raise create_query_validation_exception("limit", f"limit query parameter must be less then {max_limit}")

        return PAGINATION(offset=(index - 1) * limit, limit=limit, max_limit=max_limit, index=index)

    return pagination


class CRUDGenerator(Generic[T], APIRouter, ABC):
    schema: Type[T]
    create_schema: Type[T]
    update_schema: Type[T]
    _base_path: str = '/'

    def __init__(
            self,
            schema: Type[T],
            create_schema: Type[T] | None = None,
            update_schema: Type[T] | None = None,
            prefix: str | None = None,
            paginate: int | None = 10,
            get_all_route: bool | DEPENDENCIES = True,
            get_all_route_params: dict | None = None,
            get_one_route: bool | DEPENDENCIES = True,
            get_one_route_params: dict | None = None,
            create_route: bool | DEPENDENCIES = True,
            create_route_params: dict | None = None,
            update_route: bool | DEPENDENCIES = True,
            update_route_params: dict | None = None,
            delete_one_route: bool | DEPENDENCIES = True,
            delete_one_route_params: dict | None = None,
            delete_all_route: bool | DEPENDENCIES = True,
            delete_all_route_params: dict | None = None,
            tags: list[str] | None = None,
            *args,
            **kwargs
    ):
        """
        初始化方法
        :param schema: model模型
        :param create_schema: 创建方法的model模型，通常不带有主键
        :param update_schema: 更新方法的model模型，通常不带有主键
        :param prefix: url的前缀，并且会在doc上生成同名的文档
        :param paginate: 分页大小, 默认为10
        :param get_all_route: 是否生成获取全部数据的路由, 默认为True. 如果传入Depends列表, 则会在获取全部数据的路由上添加依赖
        :param get_all_route_params: 获取全部数据的路由的参数, 默认为None. 如果传入字典, 则会在创建路由时使用该参数
                        支持 summary、description、response_model、responses 参数
        :param get_one_route: 是否生成获取单条数据的路由, 默认为True. 如果传入Depends列表, 则会在获取单条数据的路由上添加依赖
        :param get_one_route_params: 获取单条数据的路由的参数, 默认为None. 如果传入字典, 则会在创建路由时使用该参数
        :param create_route: 是否生成创建数据的路由, 默认为True. 如果传入Depends列表, 则会在创建数据的路由上添加依赖
        :param create_route_params: 创建数据的路由的参数, 默认为None. 如果传入字典, 则会在创建路由时使用该参数
        :param update_route: 是否生成更新数据的路由, 默认为True. 如果传入Depends列表, 则会在更新数据的路由上添加依赖
        :param update_route_params: 更新数据的路由的参数, 默认为None. 如果传入字典, 则会在创建路由时使用该参数
        :param delete_one_route: 是否生成删除单条数据的路由, 默认为True. 如果传入Depends列表, 则会在删除单条数据的路由上添加依赖
        :param delete_one_route_params: 删除单条数据的路由的参数, 默认为None. 如果传入字典, 则会在创建路由时使用该参数
        :param delete_all_route: 是否生成删除全部数据的路由, 默认为True. 如果传入Depends列表, 则会在删除全部数据的路由上添加依赖
        :param delete_all_route_params: 删除全部数据的路由的参数, 默认为None. 如果传入字典, 则会在创建路由时使用该参数
        :param tags: tags名称, 默认为None. 如果传入列表, 则会在便签名称上添加便签
        :param args: 传入给父类的参数
        :param kwargs: 传入给父类的参数
        """
        self.schema = schema
        # 获取主键
        self._primary_key: str = self._primary_key if hasattr(self, "_primary_key") else "id"
        # 创建和更新的schema
        self.create_schema = create_schema if create_schema else schema_factory(self.schema, pk_field_name=self._primary_key, name=f'Create{schema.__name__.capitalize()}')
        self.update_schema = update_schema if update_schema else schema_factory(self.schema, pk_field_name=self._primary_key, name=f'Update{schema.__name__.capitalize()}')
        if prefix is None:
            prefix = self.schema.__name__
        # all prefix lowercase
        prefix = prefix.lower()
        # 便签名称和路径进行关联
        tag = prefix.strip('/')
        prefix = f'{self._base_path.strip("/")}/{tag}'
        super().__init__(prefix=prefix, tags=tags or [tag.capitalize()], *args, **kwargs)

        # 生成分页方法
        self.pagination = pagination_factory(max_limit=paginate)

        # 生成路由
        self.generate_router(
            get_all_route,
            get_all_route_params,
            get_one_route,
            get_one_route_params,
            create_route,
            create_route_params,
            update_route,
            update_route_params,
            delete_one_route,
            delete_one_route_params,
            delete_all_route,
            delete_all_route_params
        )

    def _add_api_route(
            self,
            path: str,
            endpoint: Callable[..., Any],
            dependencies: bool | DEPENDENCIES,
            methods: set[str] | list[str] | None = None,
            response_model: list[Type[T]] | Type[T] | Type[GenericModel] | None = None,
            summary: str | None = None,
            description: str | None = None,
            responses: dict[int, dict[str, Any]] | None = None,
            **kwargs: Any
    ):
        dependencies = [] if isinstance(dependencies, bool) else dependencies

        super().add_api_route(
            path,
            endpoint,
            dependencies=dependencies,
            methods=methods,
            response_model=response_model,
            summary=summary,
            description=description,
            responses=responses,
            **kwargs
        )

    def generate_router(
            self,
            get_all_route: bool | DEPENDENCIES = True,
            get_all_route_params: dict | None = None,
            get_one_route: bool | DEPENDENCIES = True,
            get_one_route_params: dict | None = None,
            create_route: bool | DEPENDENCIES = True,
            create_route_params: dict | None = None,
            update_route: bool | DEPENDENCIES = True,
            update_route_params: dict | None = None,
            delete_one_route: bool | DEPENDENCIES = True,
            delete_one_route_params: dict | None = None,
            delete_all_route: bool | DEPENDENCIES = True,
            delete_all_route_params: dict | None = None,
    ):
        if get_all_route is not False:
            summary = description = f'Get All {self.schema.__name__.capitalize()}'

            summary, description, responses, response_model = self.format_params(summary, description, get_all_route_params)

            if response_model is None:
                response_model = Sequence[self.schema]

            self._add_api_route(
                '',
                self._get_all(),
                methods=['GET'],
                response_model=response_model,
                summary=summary,
                description=description,
                dependencies=get_all_route,
                responses=responses
            )
        if create_route is not False:
            summary = description = f'Create One {self.schema.__name__.capitalize()}'

            summary, description, responses, response_model = self.format_params(summary, description, create_route_params, add_key_exist=True, add_create_fail=True)

            if response_model is None:
                response_model = self.schema

            self._add_api_route(
                '',
                self._create(),
                methods=['POST'],
                response_model=response_model,
                summary=summary,
                description=description,
                dependencies=create_route,
                responses=responses
            )
        if delete_all_route is not False:
            summary = description = f'Delete All {self.schema.__name__.capitalize()}'

            summary, description, responses, response_model = self.format_params(summary, description, delete_all_route_params)

            if response_model is None:
                response_model = Sequence[self.schema]

            self._add_api_route(
                '',
                self._delete_all(),
                methods=['DELETE'],
                response_model=response_model,
                summary=summary,
                description=description,
                dependencies=delete_all_route,
                responses=responses
            )
        if get_one_route is not False:
            summary = description = f'Get One {self.schema.__name__.capitalize()}'

            summary, description, responses, response_model = self.format_params(summary, description, get_one_route_params, add_404=True)

            if response_model is None:
                response_model = self.schema

            self._add_api_route(
                '/{item_id}',
                self._get_one(),
                methods=['GET'],
                response_model=response_model,
                summary=summary,
                description=description,
                dependencies=get_one_route,
                responses=responses
            )
        if update_route is not False:
            summary = description = f'Update One {self.schema.__name__.capitalize()}'

            summary, description, responses, response_model = self.format_params(summary, description, update_route_params, add_404=True, add_update_fail=True, add_key_exist=True)

            if response_model is None:
                response_model = self.schema

            self._add_api_route(
                '/{item_id}',
                self._update(),
                methods=['PUT'],
                response_model=response_model,
                summary=summary,
                description=description,
                dependencies=update_route,
                responses=responses
            )
        if delete_one_route is not False:
            summary = description = f'Delete One {self.schema.__name__.capitalize()}'

            summary, description, responses, response_model = self.format_params(summary, description, delete_one_route_params, add_404=True, add_delete_fail=True)

            if response_model is None:
                response_model = self.schema

            self._add_api_route(
                '/{item_id}',
                self._delete_one(),
                methods=['DELETE'],
                response_model=response_model,
                summary=summary,
                description=description,
                dependencies=delete_one_route,
                responses=responses
            )

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
        response_model = None
        if isinstance(params, dict):
            summary = params.get('summary', summary)
            description = params.get('description', description)
            responses = params.get('responses', responses)
            response_model = params.get('response_model')

        if not isinstance(responses, dict):
            responses = {}

        if add_404:
            responses[404] = {'detail': 'Not Found'}

        if add_key_exist:
            responses[522] = {'detail': 'Key Exist'}

        if add_create_fail:
            responses[523] = {'detail': 'Create Fail'}

        if add_update_fail:
            responses[524] = {'detail': 'Update Fail'}

        if add_delete_fail:
            responses[525] = {'detail': 'Delete Fail'}

        return summary, description, responses, response_model

    def api_route(self, path: str, methods: list[str] = None, *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """ Overrides and exiting route if it exists"""
        if methods is None:
            methods = ['GET']
        self.remove_api_route(path, methods)

        return super().api_route(path, methods=methods, *args, **kwargs)

    def get(self, path: str, *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        method = ['GET']
        return self.api_route(path, method, *args, **kwargs)

    def post(self, path: str, *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        method = ['POST']
        return self.api_route(path, method, *args, **kwargs)

    def put(self, path: str, *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        method = ['PUT']
        return self.api_route(path, method, *args, **kwargs)

    def delete(self, path: str, *args, **kwargs) -> Callable[[DecoratedCallable], DecoratedCallable]:
        method = ['DELETE']
        return self.api_route(path, method, *args, **kwargs)

    def remove_api_route(self, path: str, methods: list[str]):
        methods = set(methods)

        for r in self.routes:
            if r.path == f'{self.prefix}{path}' and r.methods == methods:
                self.routes.remove(r)

    @abstractmethod
    def _get_all(self, *args, **kwargs) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def _get_one(self, *args, **kwargs) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def _create(self, *args, **kwargs) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def _update(self, *args, **kwargs) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def _delete_one(self, *args, **kwargs) -> Callable:
        raise NotImplementedError

    @abstractmethod
    def _delete_all(self, *args, **kwargs) -> Callable:
        pass
