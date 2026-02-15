"""
对话记忆管理

按联系人/群维护独立上下文窗口，
避免不同会话的信息混淆，同时控制 Token 消耗。
"""
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage

from core.config import conf
from utils.logger import logger


class MemoryManager:
    """
    多会话记忆管理器

    为每个联系人/群维护独立的对话历史，
    使用滑动窗口限制保留的消息轮数。
    """

    def __init__(self, windowSize: int | None = None):
        """
        @param windowSize 每个会话保留的最大消息轮数（一问一答算2条）
        """
        self._histories: dict[str, InMemoryChatMessageHistory] = {}
        # [v12.2] 严格控制窗口大小，防止上下文污染
        base_size = windowSize or getattr(conf, 'memory_window_size', 4) or 4
        self._window_size = int(base_size) * 2

    def getHistory(self, sessionId: str) -> InMemoryChatMessageHistory:
        """
        获取指定会话的历史记录，不存在则自动创建
        """
        if sessionId not in self._histories:
            self._histories[sessionId] = InMemoryChatMessageHistory()
            logger.info(f"创建新会话记忆: {sessionId} (Window: {self._window_size})")
        return self._histories[sessionId]

    def getMessages(self, sessionId: str) -> list[BaseMessage]:
        """
        获取指定会话的历史消息列表（已截断到窗口大小）
        """
        history = self.getHistory(sessionId)
        messages = list(history.messages)

        # [v12.2] 增强滑动窗口：仅保留最近 N 条消息
        if len(messages) > self._window_size:
            trimmed = messages[-self._window_size:]
            history.clear()
            for msg in trimmed:
                history.add_message(msg)
            return trimmed

        return messages

    def addUserMessage(self, sessionId: str, content: str) -> None:
        """记录用户消息"""
        self.getHistory(sessionId).add_user_message(content)

    def addAiMessage(self, sessionId: str, content: str) -> None:
        """记录 AI 回复消息"""
        self.getHistory(sessionId).add_ai_message(content)

    def clearSession(self, sessionId: str) -> None:
        """清除指定会话的历史记录"""
        if sessionId in self._histories:
            self._histories[sessionId].clear()
            logger.info(f"已清除会话记忆: {sessionId}")

    def clearAll(self) -> None:
        """清除所有会话历史"""
        self._histories.clear()
        logger.info("已清除全部会话记忆")


# 全局记忆管理器单例
memory_manager = MemoryManager()
