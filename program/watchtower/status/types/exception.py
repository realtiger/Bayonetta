from watchtower.status.types.response import GenericBaseResponse


class SiteException(Exception):
    def __init__(self, status_code: int, response: GenericBaseResponse, headers: dict[str, str] | None = None):
        self.status_code = status_code
        self.headers = headers

        # response 初始化处理
        if response.data is None:
            response.data = dict()
        self.response = response
