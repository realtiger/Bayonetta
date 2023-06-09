from watchtower.settings.logger_config import get_logging_dict
from watchtower.settings.settings import Settings

settings = Settings()
logger = settings.get_logger()

__all__ = ['settings', 'logger']
