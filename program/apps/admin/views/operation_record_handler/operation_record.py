from apps.admin.models import OperationRecord
from apps.admin.views.operation_record_handler.operation_record_types import OperationQueryData
from oracle.sqlalchemy import SQLAlchemyCRUDRouter

router = SQLAlchemyCRUDRouter(
    OperationQueryData,
    OperationRecord,
    tags=['operation'],
    create_route=False,
    update_route=False,
    delete_one_route=False,
)
tags_metadata = [{"name": "operation", "description": "系统日志" }]
