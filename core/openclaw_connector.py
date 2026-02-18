"""
Universal OpenClaw Connector - 通用 OpenClaw 连接管理器

支持多种通信模式（通过 .env 配置切换）：
1. file    - 文件桥接（最可靠，推荐）
2. http    - HTTP 轮询（实时性好）
3. moltbook - Moltbook 私信（跨平台）
4. bridge  - 本地 Bridge 服务器（兼容性最好）
"""
import os
import json
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
from utils.logger import logger


class ConnectorMode(Enum):
    """连接模式枚举"""
    FILE = "file"           # 文件桥接
    HTTP = "http"           # HTTP 轮询
    MOLTBOOK = "moltbook"   # Moltbook 私信
    BRIDGE = "bridge"       # 本地 Bridge（默认）


@dataclass
class ConnectorConfig:
    """连接器配置"""
    mode: ConnectorMode = ConnectorMode.BRIDGE
    
    # Bridge 模式配置
    bridge_api_base: str = "http://localhost:9847"
    bridge_timeout: int = 120
    
    # File 模式配置
    file_inbox_path: str = "~/.openclaw/inbox"
    file_outbox_path: str = "~/.openclaw/outbox"
    file_poll_interval: float = 0.5  # 秒
    
    # HTTP 模式配置
    http_webhook_url: str = ""
    http_poll_interval: float = 1.0
    
    # Moltbook 模式配置
    moltbook_api_key: str = ""
    moltbook_agent_name: str = "xiaohuge"
    moltbook_poll_interval: float = 5.0
    
    @classmethod
    def from_env(cls) -> "ConnectorConfig":
        """从环境变量加载配置"""
        mode_str = os.getenv("OPENCLAW_MODE", "bridge").lower()
        
        try:
            mode = ConnectorMode(mode_str)
        except ValueError:
            logger.warning(f"未知的 OPENCLAW_MODE: {mode_str}，使用默认 bridge 模式")
            mode = ConnectorMode.BRIDGE
        
        return cls(
            mode=mode,
            bridge_api_base=os.getenv("OPENCLAW_BRIDGE_API_BASE", "http://localhost:9847"),
            bridge_timeout=int(os.getenv("OPENCLAW_BRIDGE_TIMEOUT", "120")),
            file_inbox_path=os.getenv("OPENCLAW_FILE_INBOX", "~/.openclaw/inbox"),
            file_outbox_path=os.getenv("OPENCLAW_FILE_OUTBOX", "~/.openclaw/outbox"),
            file_poll_interval=float(os.getenv("OPENCLAW_FILE_POLL_INTERVAL", "0.5")),
            http_webhook_url=os.getenv("OPENCLAW_HTTP_WEBHOOK_URL", ""),
            http_poll_interval=float(os.getenv("OPENCLAW_HTTP_POLL_INTERVAL", "1.0")),
            moltbook_api_key=os.getenv("MOLTBOOK_API_KEY", ""),
            moltbook_agent_name=os.getenv("OPENCLAW_MOLTBOOK_AGENT", "xiaohuge"),
            moltbook_poll_interval=float(os.getenv("OPENCLAW_MOLTBOOK_POLL_INTERVAL", "5.0")),
        )


class FileBridgeConnector:
    """文件桥接连接器 - 最可靠的方式"""
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.inbox_path = Path(config.file_inbox_path).expanduser()
        self.outbox_path = Path(config.file_outbox_path).expanduser()
        self._ensure_directories()
        self._last_reply_time = 0
    
    def _ensure_directories(self):
        """确保目录存在"""
        self.inbox_path.mkdir(parents=True, exist_ok=True)
        self.outbox_path.mkdir(parents=True, exist_ok=True)
    
    async def send_message(
        self, 
        message: str, 
        sender: str, 
        context: Dict[str, Any]
    ) -> str:
        """发送消息（写入 inbox）"""
        try:
            msg_file = self.inbox_path / "wechat_messages.jsonl"
            
            entry = {
                "timestamp": datetime.now().isoformat(),
                "sender": sender,
                "message": message,
                "context": context,
                "id": f"{datetime.now().timestamp()}"
            }
            
            with open(msg_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
            logger.info(f"[FileBridge] Message written to inbox: {sender}")
            
            # 等待回复（轮询 outbox）
            return await self._wait_for_reply(entry["id"])
            
        except Exception as e:
            logger.error(f"[FileBridge] Failed to send: {e}")
            return f"[Error] FileBridge: {str(e)}"
    
    async def _wait_for_reply(self, msg_id: str, timeout: int = 60) -> str:
        """等待回复"""
        reply_file = self.outbox_path / "wechat_replies.jsonl"
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            if reply_file.exists():
                try:
                    with open(reply_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    
                    for line in reversed(lines):
                        try:
                            entry = json.loads(line)
                            if entry.get("reply_to") == msg_id:
                                logger.info(f"[FileBridge] Reply found for {msg_id}")
                                return entry.get("reply", "[Empty reply]")
                        except json.JSONDecodeError:
                            continue
                            
                except Exception as e:
                    logger.warning(f"[FileBridge] Error reading reply: {e}")
            
            await asyncio.sleep(self.config.file_poll_interval)
        
        return "[Timeout] 等待回复超时，OpenClaw 代理可能未响应"


class MoltbookConnector:
    """Moltbook 私信连接器"""
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.api_base = "https://www.moltbook.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {config.moltbook_api_key}",
            "Content-Type": "application/json"
        }
    
    async def send_message(
        self, 
        message: str, 
        sender: str, 
        context: Dict[str, Any]
    ) -> str:
        """通过 Moltbook 私信发送"""
        try:
            async with aiohttp.ClientSession() as session:
                # 构建完整消息
                full_message = f"【{sender}】{message}"
                if context.get("is_voice"):
                    full_message = "[语音] " + full_message
                
                payload = {
                    "recipient": self.config.moltbook_agent_name,
                    "content": full_message
                }
                
                async with session.post(
                    f"{self.api_base}/dms",
                    headers=self.headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"[Moltbook] DM sent to {self.config.moltbook_agent_name}")
                        return "[消息已通过 Moltbook 发送给 OpenClaw 代理]"
                    else:
                        error = await resp.text()
                        logger.error(f"[Moltbook] API error: {resp.status} - {error}")
                        return f"[Moltbook Error] {resp.status}"
                        
        except Exception as e:
            logger.error(f"[Moltbook] Failed to send: {e}")
            return f"[Error] Moltbook: {str(e)}"


class HTTPConnector:
    """HTTP 连接器"""
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.webhook_url = config.http_webhook_url
    
    async def send_message(
        self, 
        message: str, 
        sender: str, 
        context: Dict[str, Any]
    ) -> str:
        """通过 HTTP Webhook 发送"""
        if not self.webhook_url:
            return "[Error] HTTP webhook URL not configured"
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": message,
                    "sender": sender,
                    "context": context,
                    "timestamp": datetime.now().isoformat()
                }
                
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("reply", "[No reply]")
                    else:
                        return f"[HTTP Error] {resp.status}"
                        
        except Exception as e:
            logger.error(f"[HTTP] Failed: {e}")
            return f"[Error] HTTP: {str(e)}"


class BridgeConnector:
    """本地 Bridge 连接器（默认）"""
    
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.api_base = config.bridge_api_base
        self.timeout = config.bridge_timeout
    
    async def send_message(
        self, 
        message: str, 
        sender: str, 
        context: Dict[str, Any]
    ) -> str:
        """通过本地 Bridge 发送"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": message,
                    "sender": sender,
                    "context": context
                }
                
                async with session.post(
                    f"{self.api_base}/api/v1/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("reply", "[Empty reply]")
                    else:
                        error = await resp.text()
                        return f"[Bridge Error] {resp.status}: {error}"
                        
        except asyncio.TimeoutError:
            return "[Timeout] Bridge 响应超时"
        except Exception as e:
            logger.error(f"[Bridge] Failed: {e}")
            return f"[Error] Bridge: {str(e)}"


class OpenClawConnector:
    """
    通用 OpenClaw 连接器
    
    根据 .env 配置自动选择通信模式
    """
    
    def __init__(self):
        self.config = ConnectorConfig.from_env()
        self._connector = self._create_connector()
        logger.info(f"[OpenClawConnector] Mode: {self.config.mode.value}")
    
    def _create_connector(self):
        """根据配置创建对应的连接器"""
        if self.config.mode == ConnectorMode.FILE:
            return FileBridgeConnector(self.config)
        elif self.config.mode == ConnectorMode.MOLTBOOK:
            return MoltbookConnector(self.config)
        elif self.config.mode == ConnectorMode.HTTP:
            return HTTPConnector(self.config)
        else:  # BRIDGE (default)
            return BridgeConnector(self.config)
    
    async def send_message(
        self, 
        message: str, 
        sender: str = "wechat-user",
        **context
    ) -> str:
        """发送消息到 OpenClaw"""
        return await self._connector.send_message(message, sender, context)
    
    def get_mode(self) -> str:
        """获取当前模式"""
        return self.config.mode.value
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if self.config.mode == ConnectorMode.BRIDGE:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.config.bridge_api_base}/health",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        return resp.status == 200
            elif self.config.mode == ConnectorMode.FILE:
                return (
                    Path(self.config.file_inbox_path).expanduser().exists() and
                    Path(self.config.file_outbox_path).expanduser().exists()
                )
            elif self.config.mode == ConnectorMode.MOLTBOOK:
                return bool(self.config.moltbook_api_key)
            else:
                return bool(self.config.http_webhook_url)
        except:
            return False


# 便捷函数
async def ask_openclaw(message: str, sender: str = "wechat-user", **context) -> str:
    """快速询问 OpenClaw"""
    connector = OpenClawConnector()
    return await connector.send_message(message, sender, **context)


def get_connector_info() -> Dict[str, Any]:
    """获取连接器信息"""
    config = ConnectorConfig.from_env()
    return {
        "mode": config.mode.value,
        "bridge_api_base": config.bridge_api_base,
        "file_inbox": config.file_inbox_path,
        "file_outbox": config.file_outbox_path,
        "moltbook_agent": config.moltbook_agent_name,
        "http_webhook": "已配置" if config.http_webhook_url else "未配置",
    }
