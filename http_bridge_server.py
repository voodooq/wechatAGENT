#!/usr/bin/env python3
"""
OpenClaw HTTP Bridge - 快速 HTTP 通信模式

与 file_bridge_monitor.py 配合使用，通过 HTTP 通信（比文件更快）
运行在我的环境中

用法:
    python http_bridge_server.py
"""

import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="OpenClaw HTTP Bridge", version="1.0.0")

# 消息队列（内存中）
message_queue = []
reply_cache = {}


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    sender: str = "wechat-user"
    context: dict = {}


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    timestamp: str


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "mode": "http",
        "pending_messages": len(message_queue),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    处理消息并等待回复
    
    这是同步接口，会等待我的回复（最多10秒）
    """
    import uuid
    msg_id = str(uuid.uuid4())[:8]
    
    # 添加消息到队列
    message_entry = {
        "id": msg_id,
        "timestamp": datetime.now().isoformat(),
        "sender": request.sender,
        "message": request.message,
        "context": request.context
    }
    message_queue.append(message_entry)
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] HTTP Message #{msg_id}")
    print(f"  From: {request.sender}")
    print(f"  Content: {request.message[:80]}{'...' if len(request.message) > 80 else ''}")
    
    # 等待回复（最多60秒）
    max_wait = 600  # 600 * 0.1s = 60秒
    for i in range(max_wait):
        if msg_id in reply_cache:
            reply = reply_cache.pop(msg_id)
            print(f"  Reply sent")
            return ChatResponse(reply=reply, timestamp=datetime.now().isoformat())
        await asyncio.sleep(0.1)
    
    # 超时，从队列移除
    message_queue[:] = [m for m in message_queue if m["id"] != msg_id]
    # 返回友好的超时提示
    timeout_reply = "抱歉，我思考的时间有点长，请稍后再试~\n\n---\n🤖 AI 生成"
    return ChatResponse(reply=timeout_reply, timestamp=datetime.now().isoformat())


@app.get("/api/v1/messages")
async def get_messages():
    """获取待处理的消息（供我调用）"""
    return {
        "messages": message_queue,
        "count": len(message_queue)
    }


@app.post("/api/v1/reply")
async def post_reply(msg_id: str, reply: str):
    """提交回复（供我调用）"""
    reply_cache[msg_id] = reply
    # 从队列移除
    message_queue[:] = [m for m in message_queue if m["id"] != msg_id]
    return {"status": "ok"}


def process_message(message: dict) -> str:
    """
    处理消息（这里是我实际回复的地方）
    
    注意：此函数会被 OpenClaw 实际调用，返回的回复会发送给用户
    """
    sender = message.get("sender", "unknown")
    content = message.get("message", "")
    
    # 简化回复，只返回核心信息 + AI 标记
    # 实际回复内容由 OpenClaw 生成，这里只是占位
    reply = f"""[OpenClaw 处理中...]

用户消息：{content}

请使用 OpenClaw 工具处理此消息并生成回复。

---
🤖 AI 生成"""
    
    return reply


async def auto_reply_worker():
    """
    自动回复工作线程
    监控消息队列并自动回复
    """
    while True:
        if message_queue:
            message = message_queue.pop(0)
            msg_id = message.get("id")
            
            # 生成回复
            reply = process_message(message)
            
            # 存入缓存
            reply_cache[msg_id] = reply
            
            print(f"  Auto-replied to #{msg_id}")
        
        await asyncio.sleep(0.05)  # 50ms检查一次


@app.on_event("startup")
async def startup():
    """启动时运行"""
    # 禁用自动回复工作线程 - 等待 OpenClaw 主动回复
    # asyncio.create_task(auto_reply_worker())
    print("  自动回复已禁用，等待 OpenClaw 处理...")


def main():
    host = os.getenv("HTTP_BRIDGE_HOST", "0.0.0.0")
    port = int(os.getenv("HTTP_BRIDGE_PORT", "9848"))
    
    print(f"""
╔════════════════════════════════════════════════╗
║     OpenClaw HTTP Bridge Server v1.0.0        ║
╠════════════════════════════════════════════════╣
║  Mode:   HTTP (Fast Mode)                      ║
║  Agent:  xiaohuge                              ║
║  Host:   {host:<36} ║
║  Port:   {port:<36} ║
╚════════════════════════════════════════════════╝

Auto-reply worker running...
Press Ctrl+C to stop
    """)
    
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
