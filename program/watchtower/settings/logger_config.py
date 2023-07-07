"""
实例化对象，作为单例模式使用，后期有所更改再进行更新。
"""
import logging
from pathlib import Path


# 日志格式类，用于Linux系统下，使控制台输出的日志带颜色
class ColorFormatter(logging.Formatter):
    log_colors = {
        'CRITICAL': '\033[0;31;47m%s\033[0m',
        'ERROR': '\033[0;33;41m%s\033[0m',
        'WARNING': '\033[0;35;46m%s\033[0m',
        'INFO': '\033[0;32m%s\033[0m',
        'DEBUG': '\033[0;00m%s\033[0m',
    }

    def format(self, record: logging.LogRecord) -> str:
        s = super().format(record)

        level_name = record.levelname
        if level_name in self.log_colors:
            return self.log_colors[level_name] % s
        return s


def get_logging_dict(log_level: str, log_dir: Path, project_name: str = "program") -> dict:
    """
    获取logging配置字典
    :param log_level: log等级
    :param log_dir: log目录
    :param project_name: 项目名称
    :return:
    """
    # 创建logs目录
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    # 设定log参数
    return {
        'version': 1,
        'disable_existing_loggers': False,
        # 日志记录格式
        'formatters': {
            'verbose': {
                'format': '%(asctime)s [%(name)s:%(levelname)s] [%(module)s:%(funcName)s:%(lineno)d] - %(message)s',
            },
            'standard': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
            'console': {
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'format': '%(asctime)s [%(name)s:%(levelname)s] [%(module)s:%(funcName)s:%(lineno)d] - %(message)s',
                # 自定义formatter样式
                # 'class': "watchtower.ColorFormatter",
            },
            'exception': {
                'datefmt': '%Y-%m-%d %H:%M:%S',
                'format': '%(asctime)s [%(levelname)s] %(message)s',
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
            'syslog': {
                'format': f'{project_name}: %(message)s'
            },
            'msg': {
                'format': '%(message)s'
            }
        },
        # 处理器
        'handlers': {
            'default': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                # 日志输出文件
                'filename': log_dir / 'all.log',
                # 文件大小
                'maxBytes': 1024 * 1024 * 5,
                # 备份份数
                'backupCount': 7,
                # 使用哪种formatters日志格式
                'formatter': 'verbose',
                "encoding": 'utf-8',
            },
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'console',
            },
            'server_handler': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'server.log',
                'maxBytes': 1024 * 1024 * 5,
                'backupCount': 7,
                'formatter': 'standard',
                "encoding": 'utf-8',
            },
            'error_handler': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'error.log',
                'maxBytes': 1024 * 1024 * 5,
                'backupCount': 7,
                'formatter': 'standard',
                "encoding": 'utf-8',
            },
        },
        'loggers': {
            # 默认的logger应用如下配置
            '': {
                'handlers': ['default', 'console'],
                'level': log_level,
                'propagate': True
            },
            project_name: {
                'handlers': ['default', 'console'],
                'level': log_level,
                'propagate': True
            },
            'server': {
                'handlers': ['server_handler'],
                'level': log_level,
                # 是否继承父类的log信息
                'propagate': True
            },
            'error': {
                'handlers': ['error_handler'],
                'level': log_level,
                # 是否继承父类的log信息
                'propagate': True
            },
        }
    }
