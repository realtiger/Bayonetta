"""
专门为Bayonetta项目封装的orm 操作层
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from watchtower import settings

logger = settings.LOGGER


