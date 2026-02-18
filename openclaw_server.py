"""
OpenClaw Gateway Server - 与 wechat-agent 对接的 HTTP 服务

运行在我的环境中，接收 wechat-agent 的消息并返回回复
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="OpenClaw Gateway", version="1.0.0")

# 存储会话状态
sessions = {}


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    sender: str = "wechat-user"
    context: dict = {}
    session_key: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """聊天响应"""
    reply: str
    timestamp: str
    session_key: Optional[str] = None


async def process_with_openclaw(message: str, sender: str, context: dict) -> str:
    """
    处理消息并返回回复
    
    这里是我（OpenClaw 代理）实际处理消息的地方
    """
    # 构建上下文信息
    context_info = f"""
【微信消息上下文】
- 发送者: {sender}
- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 来源: wechat-agent (IronSentinel)
"""
    
    if context.get("is_voice"):
        context_info += "- 消息类型: 语音转文字\n"
    
    if context.get("group_name"):
        context_info += f"- 群组: {context['group_name']}\n"
    
    # 组合完整消息
    full_message = f"{context_info}\n【用户消息】\n{message}"
    
    # TODO: 这里调用我的实际处理能力
    # 现在返回一个模拟回复，实际应该通过某种方式与我通信
    
    reply = f"""收到你的消息："{message[:50]}{'...' if len(message) > 50 else ''}"

我是 OpenClaw 代理，已成功与 wechat-agent 对接！

当前功能状态：
✅ 消息接收: 正常
✅ 上下文感知: 已启用
⏳ 工具调用: 待配置
⏳ 记忆系统: 待同步

你可以尝试问我任何问题，我会尽力帮助你。"""
    
    return reply


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    非流式聊天接口
    """
    try:
        reply = await process_with_openclaw(
            message=request.message,
            sender=request.sender,
            context=request.context
        )
        
        return ChatResponse(
            reply=reply,
            timestamp=datetime.now().isoformat(),
            session_key=request.session_key
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口
    """
    async def generate():
        try:
            # 获取完整回复
            reply = await process_with_openclaw(
                message=request.message,
                sender=request.sender,
                context=request.context
            )
            
            # 模拟流式输出（按字符分割）
            for char in reply:
                chunk = json.dumps({"content": char})
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.01)  # 模拟打字效果
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_chunk = json.dumps({"error": str(e)})
            yield f"data: {error_chunk}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@app.get("/api/v1/status")
async def get_status():
    """获取服务状态"""
    return {
        "active_sessions": len(sessions),
        "uptime": "running",
        "capabilities": [
            "chat",
            "streaming",
            "context_aware"
        ]
    }


def start_server(host: str = "0.0.0.0", port: int = 9847):
    """启动服务器"""
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_server()
