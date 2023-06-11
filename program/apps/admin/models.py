from sqlalchemy import Column, BigInteger, String

from oracle.sqlalchemy import SiteBaseModel


# 操作记录
class OperationRecord(SiteBaseModel):
    __tablename__ = "operation_record"

    user_id = Column(BigInteger, comment="用户id")
    data = Column(String(512), comment="请求数据")
