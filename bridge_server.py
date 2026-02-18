#!/usr/bin/env python3
"""
OpenClaw Agent Bridge Server - 文件桥接版本

通过文件系统与我（xiaohuge）通信：
1. 收到消息 -> 写入 inbox/wechat_messages.jsonl
2. 等待我的回复 -> 从 outbox/wechat_replies.jsonl 读取
3. 返回回复给 wechat-agent

运行: python bridge_server.py
"""

import os
import sys
import json
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    import uvicorn
    import aiohttp
except ImportError:
    print("Installing dependencies...")
    os.system(f"{sys.executable} -m pip install fastapi uvicorn aiohttp pydantic -q")
    print("Please restart the script")
    sys.exit(0)

app = FastAPI(title="OpenClaw Agent Bridge", version="2.0.0")

# 文件桥接配置
# 支持从环境变量配置路径，适应不同环境
# 默认使用当前目录下的 .openclaw 文件夹
# Windows: E:\work\wechatAGENT\.openclaw
# Docker: /home/node/openclaw/wechat-agent/.openclaw
PROJECT_ROOT = Path(__file__).parent.resolve()
DEFAULT_INBOX = PROJECT_ROOT / ".openclaw" / "inbox"
DEFAULT_OUTBOX = PROJECT_ROOT / ".openclaw" / "outbox"

# 可以从环境变量覆盖路径（用于跨平台）
INBOX_PATH = Path(os.getenv("OPENCLAW_INBOX", DEFAULT_INBOX))
OUTBOX_PATH = Path(os.getenv("OPENCLAW_OUTBOX", DEFAULT_OUTBOX))

# 确保目录存在
INBOX_PATH.mkdir(parents=True, exist_ok=True)
OUTBOX_PATH.mkdir(parents=True, exist_ok=True)


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    sender: str = "wechat-user"
    context: dict = {}
    session_key: Optional[str] = None
    stream: bool = False


async def forward_via_file_bridge(message: str, sender: str, context: dict) -> str:
    """
    通过文件桥接转发消息并等待回复
    
    流程:
    1. 写入消息到 inbox
    2. 轮询 outbox 等待回复（最多60秒）
    3. 返回回复内容
    """
    msg_id = str(uuid.uuid4())[:8]
    
    # 1. 写入消息到 inbox
    message_file = INBOX_PATH / "wechat_messages.jsonl"
    entry = {
        "id": msg_id,
        "timestamp": datetime.now().isoformat(),
        "sender": sender,
        "message": message,
        "context": context
    }
    
    try:
        with open(message_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Message #{msg_id} written to inbox")
    except Exception as e:
        print(f"Error writing to inbox: {e}")
        return f"[Error] Failed to write message: {e}"
    
    # 2. 轮询等待回复（最多30秒，轮询间隔0.1秒）
    reply_file = OUTBOX_PATH / "wechat_replies.jsonl"
    start_time = datetime.now()
    max_wait = 30  # 减少到30秒
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for reply #{msg_id}...")
    
    # 先等待1秒给处理时间
    await asyncio.sleep(1)
    
    while (datetime.now() - start_time).seconds < max_wait:
        if reply_file.exists():
            try:
                with open(reply_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                # 查找对应 msg_id 的回复
                for line in reversed(lines):
                    try:
                        reply_entry = json.loads(line.strip())
                        if reply_entry.get("reply_to") == msg_id:
                            reply = reply_entry.get("reply", "[Empty reply]")
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Reply #{msg_id} found")
                            return reply
                    except json.JSONDecodeError:
                        continue
                        
            except Exception as e:
                print(f"Error reading reply file: {e}")
        
        # 等待后重试（100ms轮询）
        await asyncio.sleep(0.1)
    
    # 超时
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Timeout waiting for reply #{msg_id}")
    return "[Timeout] OpenClaw agent did not respond within 30 seconds. The agent may be offline or the file bridge is not synchronized.\n\nPossible solutions:\n1. Check if the file bridge monitor is running\n2. Switch to HTTP mode for faster response\n3. Check file permissions between Windows and Docker"


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "mode": "file_bridge",
        "inbox": str(INBOX_PATH),
        "outbox": str(OUTBOX_PATH),
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """非流式聊天接口"""
    try:
        reply = await forward_via_file_bridge(
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
            reply = await forward_via_file_bridge(
                message=request.message,
                sender=request.sender,
                context=request.context
            )
            
            # 模拟流式输出
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
    inbox_count = 0
    outbox_count = 0
    
    try:
        msg_file = INBOX_PATH / "wechat_messages.jsonl"
        if msg_file.exists():
            with open(msg_file, "r", encoding="utf-8") as f:
                inbox_count = len(f.readlines())
    except:
        pass
    
    try:
        reply_file = OUTBOX_PATH / "wechat_replies.jsonl"
        if reply_file.exists():
            with open(reply_file, "r", encoding="utf-8") as f:
                outbox_count = len(f.readlines())
    except:
        pass
    
    return {
        "agent_name": "xiaohuge",
        "mode": "file_bridge",
        "inbox_path": str(INBOX_PATH),
        "outbox_path": str(OUTBOX_PATH),
        "inbox_messages": inbox_count,
        "outbox_replies": outbox_count,
        "timestamp": datetime.now().isoformat()
    }


def main():
    """主函数"""
    host = os.getenv("BRIDGE_HOST", "127.0.0.1")
    port = int(os.getenv("BRIDGE_PORT", "9847"))
    
    print(f"""
╔════════════════════════════════════════════════╗
║     OpenClaw Agent Bridge Server v2.0.0       ║
╠════════════════════════════════════════════════╣
║  Mode:   File Bridge                           ║
║  Agent:  xiaohuge                              ║
║  Host:   {host:<36} ║
║  Port:   {port:<36} ║
╠════════════════════════════════════════════════╣
║  Inbox:  {str(INBOX_PATH):<36} ║
║  Outbox: {str(OUTBOX_PATH):<36} ║
╚════════════════════════════════════════════════╝

Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Press Ctrl+C to stop
    """)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
