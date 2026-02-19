#!/usr/bin/env python3
"""
OpenClaw HTTP Bridge - OpenClaw 直连模式

工作方式：
1. 接收 wechat-agent 的消息 → 存入队列
2. OpenClaw 定期轮询 /api/v1/messages 获取消息
3. OpenClaw 处理完成后调用 /api/v1/reply 提交回复
4. wechat-agent 获取回复

用法:
    python http_bridge_server.py
    
OpenClaw 端配置:
    设置环境变量 OPENCLAW_BRIDGE_URL=http://host.docker.internal:9848
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("Installing dependencies...")
    os.system(f"{sys.executable} -m pip install fastapi uvicorn pydantic -q")
    print("Please restart the script")
    sys.exit(0)

app = FastAPI(title="OpenClaw HTTP Bridge", version="3.0.0")

# 消息队列和回复缓存
message_queue: list = []
reply_cache: Dict[str, str] = {}
processed_messages: set = set()  # 已处理的消息 ID

# 统计数据
stats = {
    "total_received": 0,
    "total_replied": 0,
    "start_time": datetime.now().isoformat()
}


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    sender: str = "wechat-user"
    context: dict = {}


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    timestamp: str


class ReplyRequest(BaseModel):
    """回复提交请求"""
    msg_id: str
    reply: str


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "mode": "openclaw-direct",
        "pending_messages": len(message_queue),
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    接收消息并等待 OpenClaw 回复
    
    这是同步接口，会等待 OpenClaw 的回复（最多 120 秒）
    """
    import uuid
    msg_id = str(uuid.uuid4())[:8]
    
    # 检查是否已处理过（去重）
    if msg_id in processed_messages:
        return ChatResponse(
            reply="[Duplicate] 消息已处理",
            timestamp=datetime.now().isoformat()
        )
    
    # 添加消息到队列
    message_entry = {
        "id": msg_id,
        "timestamp": datetime.now().isoformat(),
        "sender": request.sender,
        "message": request.message,
        "context": request.context,
        "status": "pending"  # pending, processing, completed
    }
    message_queue.append(message_entry)
    stats["total_received"] += 1
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📥 收到消息 #{msg_id}")
    print(f"  From: {request.sender}")
    print(f"  Content: {request.message[:60]}{'...' if len(request.message) > 60 else ''}")
    print(f"  等待 OpenClaw 处理...")
    
    # 等待回复（最多 120 秒）
    max_wait = 1200  # 1200 * 0.1s = 120 秒
    for i in range(max_wait):
        if msg_id in reply_cache:
            reply = reply_cache.pop(msg_id)
            processed_messages.add(msg_id)
            stats["total_replied"] += 1
            print(f"  ✅ 消息 #{msg_id} 已完成")
            return ChatResponse(reply=reply, timestamp=datetime.now().isoformat())
        await asyncio.sleep(0.1)
    
    # 超时
    message_queue[:] = [m for m in message_queue if m["id"] != msg_id]
    timeout_reply = "抱歉，响应超时了，请稍后再试~\n\n---\n🤖 AI 生成"
    return ChatResponse(reply=timeout_reply, timestamp=datetime.now().isoformat())


@app.get("/api/v1/messages")
async def get_messages():
    """
    获取待处理的消息列表（供 OpenClaw 轮询）
    
    OpenClaw 应该定期调用此接口获取新消息
    """
    pending = [m for m in message_queue if m["status"] == "pending"]
    return {
        "messages": pending,
        "count": len(pending),
        "stats": stats
    }


@app.post("/api/v1/messages/{msg_id}/status")
async def update_message_status(msg_id: str, status: str):
    """更新消息状态（OpenClaw 开始处理时调用）"""
    for msg in message_queue:
        if msg["id"] == msg_id:
            msg["status"] = status
            print(f"  🔄 消息 #{msg_id} 状态更新为: {status}")
            return {"status": "ok"}
    return {"status": "error", "message": "Message not found"}


@app.post("/api/v1/reply")
async def post_reply(request: ReplyRequest):
    """
    提交回复（供 OpenClaw 调用）
    
    OpenClaw 处理完消息后，调用此接口提交回复
    """
    reply_cache[request.msg_id] = request.reply
    
    # 更新消息状态
    for msg in message_queue:
        if msg["id"] == request.msg_id:
            msg["status"] = "completed"
            break
    
    print(f"  📤 收到回复 #{request.msg_id} (长度: {len(request.reply)})")
    return {"status": "ok", "msg_id": request.msg_id}


@app.delete("/api/v1/messages/{msg_id}")
async def delete_message(msg_id: str):
    """删除已处理的消息"""
    global message_queue
    message_queue = [m for m in message_queue if m["id"] != msg_id]
    return {"status": "ok"}


def main():
    host = os.getenv("HTTP_BRIDGE_HOST", "0.0.0.0")
    port = int(os.getenv("HTTP_BRIDGE_PORT", "9848"))
    
    print(f"""
╔════════════════════════════════════════════════╗
║     OpenClaw HTTP Bridge Server v3.0.0        ║
╠════════════════════════════════════════════════╣
║  Mode:   OpenClaw Direct Connection            ║
║  Host:   {host:<36} ║
║  Port:   {port:<36} ║
╚════════════════════════════════════════════════╝

📋 OpenClaw 端配置:
   export OPENCLAW_BRIDGE_URL=http://host.docker.internal:{port}
   
🔄 工作流:
   1. wechat-agent 发送消息到 /api/v1/chat
   2. OpenClaw 轮询 /api/v1/messages 获取消息
   3. OpenClaw 处理完成后 POST /api/v1/reply
   4. wechat-agent 收到回复

Press Ctrl+C to stop
    """)
    
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
