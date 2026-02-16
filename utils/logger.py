"""
AI 智能助理 - 日志系统

统一日志格式，支持按日期滚动和多级别输出。
"""
import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

from core.config import conf


def setupLogger(name: str = "ai_assistant") -> logging.Logger:
    """
    初始化并返回配置好的 Logger 实例

    @param name Logger 名称
    @returns 配置完成的 Logger
    """
    logger = logging.getLogger(name)

    # 避免重复初始化
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, conf.log_level.upper(), logging.INFO))

    # 统一日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出（按天滚动，保留 30 天）
    log_dir = conf.project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = TimedRotatingFileHandler(
        filename=log_dir / "assistant.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def getDailyLogger() -> logging.Logger:
    """
    获取每日消息记录专用 Logger

    用于将白名单消息写入每日日志文件，
    供摘要生成器使用。
    """
    logger = logging.getLogger("daily_messages")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    daily_dir = conf.project_root / "logs" / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    file_handler = TimedRotatingFileHandler(
        filename=daily_dir / "messages.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# 全局 Logger 代理 (v10.1 Lazy Initialization)
class LoggerProxy:
    def __init__(self, factory, name):
        self._factory = factory
        self._name = name
        self._instance = None

    def __getattr__(self, name):
        if self._instance is None:
            self._instance = self._factory(self._name)
        return getattr(self._instance, name)

# 导出代理实例，避免在导入时立即触发 setupLogger
logger = LoggerProxy(setupLogger, "ai_assistant")
daily_logger = LoggerProxy(getDailyLogger, "daily_messages")

