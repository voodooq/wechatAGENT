"""
IronSentinel - 审计日志模块

记录所有关键操作行为，用于溯源和安全审计。
"""
import sqlite3
from typing import Optional

from core.config import conf
from utils.logger import logger


class AuditLogger:
    """
    审计日志记录器

    将所有工具调用、权限变更和异常行为持久化记录到数据库。
    """

    def __init__(self):
        self._db_path = conf.db_full_path

    def _get_db_conn(self):
        return sqlite3.connect(self._db_path)

    def log_action(
        self,
        user: str,
        command: str,
        action_taken: Optional[str] = None,
        status: str = "SUCCESS"
    ) -> None:
        """
        记录一次行为

        @param user 操作人备注名
        @param command 原始指令
        @param action_taken AI 调用的工具名或执行的操作
        @param status 执行状态 (SUCCESS/FAIL/DENIED)
        """
        try:
            with self._get_db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO audit_logs (user, command, action_taken, status) VALUES (?, ?, ?, ?)",
                    (user, command, action_taken, status)
                )
                conn.commit()
                logger.debug(f"审计记录: {user} | {action_taken} | {status}")
        except Exception as e:
            logger.error(f"审计日志写入失败: {e}")

    def get_recent_logs(self, limit: int = 10):
        """获取最近的审计记录"""
        try:
            with self._get_db_conn() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT user, command, action_taken, status, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"查询审计日志失败: {e}")
            return []


# 全局审计记录器单例
audit_logger = AuditLogger()
