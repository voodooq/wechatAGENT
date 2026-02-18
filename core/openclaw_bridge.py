"""
OpenClaw Bridge - 与 OpenClaw 代理通信的桥接模块

提供 HTTP API 方式与 OpenClaw 代理进行对话
"""
import os
import json
import asyncio
import aiohttp
from typing import Optional, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from utils.logger import logger


@dataclass
class OpenClawConfig:
    """OpenClaw 配置"""
    api_base: str = "http://localhost:9847"  # OpenClaw 网关地址
    session_key: str = ""  # 会话密钥
    timeout: int = 120  # 超时时间（秒）
    
    @classmethod
    def from_env(cls) -> "OpenClawConfig":
        """从环境变量加载配置"""
        return cls(
            api_base=os.getenv("OPENCLAW_API_BASE", "http://localhost:9847"),
            session_key=os.getenv("OPENCLAW_SESSION_KEY", ""),
            timeout=int(os.getenv("OPENCLAW_TIMEOUT", "120")),
        )


class OpenClawBridge:
    """
    OpenClaw 桥接器
    
    负责与 OpenClaw 代理进行 HTTP 通信
    """
    
    def __init__(self, config: Optional[OpenClawConfig] = None):
        self.config = config or OpenClawConfig.from_env()
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def send_message(
        self, 
        message: str, 
        sender: str = "wechat-user",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        发送消息给 OpenClaw 代理并获取回复
        
        Args:
            message: 用户消息内容
            sender: 发送者标识
            context: 额外上下文信息
            
        Returns:
            OpenClaw 代理的回复文本
        """
        try:
            session = await self._get_session()
            
            payload = {
                "message": message,
                "sender": sender,
                "context": context or {},
                "session_key": self.config.session_key,
            }
            
            logger.info(f"Sending message to OpenClaw: {message[:50]}...")
            
            async with session.post(
                f"{self.config.api_base}/api/v1/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    reply = data.get("reply", "")
                    logger.info(f"Received reply from OpenClaw: {reply[:50]}...")
                    return reply
                else:
                    error_text = await response.text()
                    logger.error(f"OpenClaw API error: {response.status} - {error_text}")
                    return f"[OpenClaw Error] HTTP {response.status}: {error_text}"
                    
        except asyncio.TimeoutError:
            logger.error("OpenClaw request timeout")
            return "[Error] 请求 OpenClaw 超时，请稍后重试"
        except Exception as e:
            logger.error(f"Failed to communicate with OpenClaw: {e}")
            return f"[Error] 无法连接到 OpenClaw: {str(e)}"
    
    async def send_message_stream(
        self,
        message: str,
        sender: str = "wechat-user",
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式发送消息给 OpenClaw 代理
        
        Args:
            message: 用户消息内容
            sender: 发送者标识
            context: 额外上下文信息
            
        Yields:
            回复文本片段
        """
        try:
            session = await self._get_session()
            
            payload = {
                "message": message,
                "sender": sender,
                "context": context or {},
                "session_key": self.config.session_key,
                "stream": True,
            }
            
            async with session.post(
                f"{self.config.api_base}/api/v1/chat/stream",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk.get('content', '')
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
                else:
                    error_text = await response.text()
                    yield f"[OpenClaw Error] HTTP {response.status}"
                    
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"[Error] {str(e)}"
    
    async def health_check(self) -> bool:
        """检查 OpenClaw 服务是否可用"""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.config.api_base}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except:
            return False
    
    async def close(self):
        """关闭连接"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class OpenClawChatModel:
    """
    兼容 LangChain 的 OpenClaw 聊天模型封装
    
    可以像其他 LangChain 模型一样使用
    """
    
    def __init__(
        self,
        api_base: Optional[str] = None,
        session_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self.config = OpenClawConfig(
            api_base=api_base or os.getenv("OPENCLAW_API_BASE", "http://localhost:9847"),
            session_key=session_key or os.getenv("OPENCLAW_SESSION_KEY", ""),
        )
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._bridge = OpenClawBridge(self.config)
    
    async def ainvoke(self, prompt: str, **kwargs) -> str:
        """异步调用"""
        sender = kwargs.get("sender", "wechat-user")
        context = kwargs.get("context", {})
        return await self._bridge.send_message(prompt, sender, context)
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """同步调用（阻塞）"""
        return asyncio.run(self.ainvoke(prompt, **kwargs))
    
    async def health_check(self) -> bool:
        """健康检查"""
        return await self._bridge.health_check()


# 便捷函数
async def ask_openclaw(
    message: str,
    sender: str = "wechat-user",
    **kwargs
) -> str:
    """
    快速询问 OpenClaw 代理
    
    Args:
        message: 消息内容
        sender: 发送者
        **kwargs: 其他参数
        
    Returns:
        OpenClaw 的回复
    """
    bridge = OpenClawBridge()
    return await bridge.send_message(message, sender, kwargs)
