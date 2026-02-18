"""
OpenClaw HTTP Client - 连接 HTTP Bridge Server

运行在 wechat-agent 端，连接 http_bridge_server.py
比文件桥接更快！
"""
import os
import asyncio
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime


class OpenClawHTTPClient:
    """HTTP 客户端连接器"""
    
    def __init__(self, api_base: str = "http://localhost:9848"):
        self.api_base = api_base
        self.timeout = 15  # 15秒超时
    
    async def send_message(
        self, 
        message: str, 
        sender: str = "wechat-user",
        **context
    ) -> str:
        """发送消息并获取回复"""
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
                    elif resp.status == 504:
                        return "[Timeout] OpenClaw HTTP bridge timeout"
                    else:
                        error = await resp.text()
                        return f"[HTTP Error] {resp.status}: {error}"
                        
        except asyncio.TimeoutError:
            return "[Timeout] HTTP request timeout (15s)"
        except Exception as e:
            return f"[Error] HTTP client: {str(e)}"
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base}/health",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as resp:
                    return resp.status == 200
        except:
            return False


# 便捷函数
async def ask_openclaw_http(message: str, sender: str = "wechat-user", **context) -> str:
    """快速询问 OpenClaw（HTTP模式）"""
    api_base = os.getenv("OPENCLAW_HTTP_API", "http://localhost:9848")
    client = OpenClawHTTPClient(api_base)
    return await client.send_message(message, sender, **context)
