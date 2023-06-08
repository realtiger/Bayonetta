from .types.response import Status, success_status, common_error_status


class StatusMap:
    SUCCESS = success_status
    IDENTIFY_INVALID = Status("E00002", '用户信息错误，请确认信息是否正确')
    # ITEM_NOT_FOUND = Status("E00002", '用户信息错误，请确认信息是否正确')
    USER_NOT_ACTIVE = Status("E00003", '账户异常，用户没有启用')
    LOGIN_FAILED = Status("E00004", '用户登录失败，请联系管理员确认问题原因')
    INVALIDATE_CREDENTIALS = Status("E00005", '用户认证失败，请重新登录')
    EXPIRED_CREDENTIALS = Status("E00006", '用户认证过期，请重新登录')
    SCOPE_NOT_AUTHORIZED = Status("E00007", '用户权限不足，请申请后访问')
    GET_CACHE_ERROR = Status("E00011", '获取缓存失败')

    # 通用错误
    COMMON_ERROR = common_error_status
