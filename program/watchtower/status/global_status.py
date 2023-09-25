from watchtower.status.types.response import success_status, Status, common_error_status


class StatusMap:
    SUCCESS = success_status
    IDENTIFY_INVALID = Status("E00002", '用户信息错误，请确认信息是否正确')
    USER_NOT_ACTIVE = Status("E00003", '账户异常，用户没有启用')
    LOGIN_FAILED = Status("E00004", '用户登录失败，请联系管理员确认问题原因')
    INVALIDATE_CREDENTIALS = Status("E00005", '用户认证失败，请重新登录')
    EXPIRED_CREDENTIALS = Status("E00006", '用户认证过期，请重新登录')
    SCOPE_NOT_AUTHORIZED = Status("E00007", '用户权限不足，请申请后访问')
    FORBIDDEN = Status("E00008", '没有访问权限，请联系管理员进行添加')
    ONLY_SUPERUSER = Status("E00009", '只有管理员用户才能操作，请添加对应权限进行操作')
    CURRENT_USER_NOT_PERMISSION = Status("E00010", '当前用户没有权限')
    GET_CACHE_ERROR = Status("E00011", '获取缓存失败')
    ITEM_NOT_FOUND = Status("E00021", '未找到对应的数据')
    MULTIPLE_RESULTS_FOUND = Status("E00022", '找到多条数据')
    PRIMARY_KEY_EXISTED = Status("E00023", '主键已存在')
    CREATE_FAILED = Status("E00024", '创建失败')
    UPDATE_FAILED = Status("E00025", '更新失败')
    DELETE_FAILED = Status("E00026", '删除失败')
    DATA_VALIDATION_FAILED = Status("E00027", '数据校验失败')
    KUBE_GET_RESOURCE_FAILED = Status("E00028", '获取k8s资源失败')

    # 通用错误
    COMMON_ERROR = common_error_status
