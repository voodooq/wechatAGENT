"""
每日摘要生成器

定时读取当日消息日志，
调用 Gemini 生成摘要并发送给指定接收人。
"""
import time
import threading
from pathlib import Path
from datetime import datetime

import schedule
from core.config import conf
from core.agent import create_llm
from wechat.sender import sender
from utils.logger import logger


# 摘要生成的提示词
SUMMARY_PROMPT = """请对以下微信聊天记录进行整理和摘要。

要求：
1. 提取所有**待办事项**和**行动项**
2. 总结**重要决策**和**关键讨论**
3. 列出**需要跟进**的事项
4. 按重要程度排序
5. 使用简洁的条目式格式，适合快速阅读

聊天记录如下：
---
{messages}
---

请生成今日摘要："""


class DailySummaryScheduler:
    """
    每日摘要调度器

    使用 schedule 库在指定时间触发摘要生成任务，
    读取当日消息日志并调用 AI 整理。
    """

    def __init__(self):
        self._running = False
        self._thread: threading.Thread | None = None

    def _getDailyLogPath(self) -> Path:
        """获取当日消息日志文件路径"""
        daily_dir = conf.project_root / "logs" / "daily"
        # NOTE: TimedRotatingFileHandler 的当前日志文件名固定为 messages.log
        return daily_dir / "messages.log"

    def _readDailyMessages(self) -> str:
        """读取当日消息日志内容"""
        log_path = self._getDailyLogPath()
        if not log_path.exists():
            return ""

        try:
            content = log_path.read_text(encoding="utf-8")
            return content.strip()
        except Exception as e:
            logger.error(f"读取每日日志失败: {e}")
            return ""

    def _generateSummary(self, messages: str) -> str:
        """
        调用 Gemini 生成消息摘要

        @param messages 当日消息文本
        @returns 生成的摘要文本
        """
        try:
            # [Fix v10.2.7] 使用模型工厂创建 LLM
            llm = create_llm(temperature=0.3)

            prompt_text = SUMMARY_PROMPT.format(messages=messages)
            response = llm.invoke(prompt_text)
            return response.content

        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return f"摘要生成失败: {e}"

    def _executeSummaryTask(self) -> None:
        """执行每日摘要任务"""
        logger.info("开始执行每日摘要任务...")

        messages = self._readDailyMessages()
        if not messages:
            logger.info("今日无消息记录，跳过摘要生成")
            return

        # 生成摘要
        today = datetime.now().strftime("%Y-%m-%d")
        provider = getattr(conf, 'llm_provider', 'AI').capitalize()
        logger.info(f"正在调用 {provider} 生成每日摘要...")
        summary = self._generateSummary(messages)

        # 添加日期标题
        full_summary = f"📋 {today} 每日摘要\n{'=' * 20}\n\n{summary}"

        # 发送给指定接收人
        try:
            sender.sendMessage(
                receiver=conf.summary_receiver,
                content=full_summary,
            )
            logger.info(f"每日摘要已发送给 [{conf.summary_receiver}]")
        except Exception as e:
            logger.error(f"摘要发送失败: {e}")

        # 保存摘要到文件
        try:
            summary_dir = conf.project_root / "logs" / "summaries"
            summary_dir.mkdir(parents=True, exist_ok=True)
            summary_file = summary_dir / f"summary_{today}.txt"
            summary_file.write_text(full_summary, encoding="utf-8")
            logger.info(f"摘要已保存至: {summary_file}")
        except Exception as e:
            logger.error(f"摘要保存失败: {e}")

    def _scheduleLoop(self):
        """定时任务运行循环"""
        # 注册每日定时任务
        schedule.every().day.at(conf.summary_time).do(self._executeSummaryTask)
        logger.info(f"每日摘要任务已注册，触发时间: {conf.summary_time}")

        while self._running:
            schedule.run_pending()
            time.sleep(30)  # 每 30 秒检查一次

    def start(self) -> None:
        """启动调度器线程"""
        if self._running:
            logger.warning("调度器已在运行中")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._scheduleLoop,
            name="DailySummaryScheduler",
            daemon=True,
        )
        self._thread.start()
        logger.info("每日摘要调度器已启动")

    def stop(self) -> None:
        """停止调度器"""
        self._running = False
        schedule.clear()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("每日摘要调度器已停止")

    def triggerNow(self) -> None:
        """手动触发一次摘要生成（用于测试）"""
        self._executeSummaryTask()

    @property
    def isRunning(self) -> bool:
        return self._running
