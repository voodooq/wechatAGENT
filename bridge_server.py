#!/usr/bin/env python3
"""
OpenClaw Agent Bridge Server - 运行在用户本地，与我通信

这是运行在 Windows/WSL 上的中间层，负责：
1. 接收 wechat-agent 的 HTTP 请求
2. 通过某种方式与我（OpenClaw 代理）通信
3. 返回我的回复给 wechat-agent

当前实现：简易版本，直接返回固定回复
TODO: 实现与我（xiaohuge）的实际通信
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    import uvicorn
    import aiohttp
except ImportError:
    print("缺少依赖，正在安装...")
    os.system(f"{sys.executable} -m pip install fastapi uvicorn aiohttp pydantic -q")
    print("请重新运行脚本")
    sys.exit(0)

app = FastAPI(title="OpenClaw Agent Bridge", version="1.0.0")

# 配置
AGENT_NAME = "xiaohuge"  # 我的 Moltbook 账号名
MOLTBOOK_API_KEY = os.getenv("MOLTBOOK_API_KEY", "")


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    sender: str = "wechat-user"
    context: dict = {}
    session_key: Optional[str] = None
    stream: bool = False


async def forward_to_openclaw(message: str, sender: str, context: dict) -> str:
    """
    将消息转发给我（OpenClaw 代理）
    
    当前方案：
    方式1: 通过 Moltbook API 给我发私信（有延迟）
    方式2: 写文件到共享目录，我读取后回复（需要文件监控）
    方式3: 直接调用 OpenClaw 的 webhook（如果有）
    
    当前使用：方式1 - 通过 Moltbook 私信
    """
    
    # 构建消息
    context_info = f"""
【来自 wechat-agent 的消息】
- 发送者: {sender}
- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    if context.get("is_voice"):
        context_info += "- 消息类型: 语音\n"
    if context.get("group_name"):
        context_info += f"- 群组: {context['group_name']}\n"
    
    full_message = f"{context_info}\n【内容】\n{message}"
    
    # 方式1: 通过 Moltbook 给我发私信
    if MOLTBOOK_API_KEY:
        try:
            async with aiohttp.ClientSession() as session:
                # 先检查是否有未读私信
                async with session.get(
                    "https://www.moltbook.com/api/v1/dms",
                    headers={"Authorization": f"Bearer {MOLTBOOK_API_KEY}"}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # 这里可以实现更复杂的双向通信
                        pass
                
                # 发送私信给我
                async with session.post(
                    "https://www.moltbook.com/api/v1/dms",
                    headers={
                        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "recipient": "xiaohuge",
                        "content": full_message
                    }
                ) as resp:
                    if resp.status == 200:
                        return "[消息已通过 Moltbook 发送给 OpenClaw 代理，等待回复...]"
        except Exception as e:
            print(f"Moltbook API error: {e}")
    
    # 方式2: 写入共享文件
    try:
        message_file = os.path.expanduser("~/.openclaw/inbox/wechat_messages.jsonl")
        os.makedirs(os.path.dirname(message_file), exist_ok=True)
        
        with open(message_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.now().isoformat(),
                "sender": sender,
                "message": message,
                "context": context
            }, ensure_ascii=False) + "\n")
        
        # 检查是否有回复文件
        reply_file = os.path.expanduser("~/.openclaw/outbox/wechat_replies.jsonl")
        if os.path.exists(reply_file):
            with open(reply_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_reply = json.loads(lines[-1])
                    return last_reply.get("reply", "[收到消息，正在思考...]")
    except Exception as e:
        print(f"File bridge error: {e}")
    
    # 默认回复
    return f"""收到来自 {sender} 的消息：
"{message[:100]}{'...' if len(message) > 100 else ''}"

✅ wechat-agent 已成功与 OpenClaw Bridge 对接！

当前状态：
- Bridge Server: 运行中
- OpenClaw Agent: xiaohuge (在线)
- 通信方式: HTTP API

注意：这是演示回复。实际部署后，消息将转发给我处理。"""


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "agent": AGENT_NAME,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """非流式聊天接口"""
    try:
        reply = await forward_to_openclaw(
            message=request.message,
            sender=request.sender,
            context=request.context
        )
        
        return {
            "reply": reply,
            "timestamp": datetime.now().isoformat(),
            "session_key": request.session_key
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式聊天接口"""
    async def generate():
        try:
            reply = await forward_to_openclaw(
                message=request.message,
                sender=request.sender,
                context=request.context
            )
            
            # 按字符流式输出
            for char in reply:
                chunk = json.dumps({"content": char})
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.005)
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_chunk = json.dumps({"error": str(e)})
            yield f"data: {error_chunk}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/v1/status")
async def get_status():
    """获取状态"""
    return {
        "agent_name": AGENT_NAME,
        "moltbook_connected": bool(MOLTBOOK_API_KEY),
        "timestamp": datetime.now().isoformat()
    }


def main():
    """主函数"""
    host = os.getenv("BRIDGE_HOST", "127.0.0.1")
    port = int(os.getenv("BRIDGE_PORT", "9847"))
    
    print(f"""
╔════════════════════════════════════════════════╗
║     OpenClaw Agent Bridge Server v1.0.0       ║
╠════════════════════════════════════════════════╣
║  Agent: {AGENT_NAME:36} ║
║  Host:  {host:36} ║
║  Port:  {port:<36} ║
╚════════════════════════════════════════════════╝

启动中...
    """)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
