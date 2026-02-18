#!/usr/bin/env python3
"""
OpenClaw File Bridge Monitor - 文件桥接监听器

监控 inbox 文件，处理消息后写入 outbox
运行在我的环境中

用法:
    python file_bridge_monitor.py
"""

import os
import json
import asyncio
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# 桥接路径（与 Bridge Server 共享）
# 使用环境变量或默认值
PROJECT_ROOT = Path("/home/node/openclaw/wechat-agent")
INBOX_PATH = Path(os.getenv("OPENCLAW_INBOX", PROJECT_ROOT / ".openclaw" / "inbox"))
OUTBOX_PATH = Path(os.getenv("OPENCLAW_OUTBOX", PROJECT_ROOT / ".openclaw" / "outbox"))


class FileBridgeMonitor:
    """文件桥接监听器"""
    
    def __init__(self):
        self.inbox_file = INBOX_PATH / "wechat_messages.jsonl"
        self.outbox_file = OUTBOX_PATH / "wechat_replies.jsonl"
        self.processed_ids = set()
        self.last_position = 0
        
        # 确保目录存在
        INBOX_PATH.mkdir(parents=True, exist_ok=True)
        OUTBOX_PATH.mkdir(parents=True, exist_ok=True)
    
    async def process_message(self, entry: Dict[str, Any]) -> str:
        """
        处理消息并生成回复
        
        这里调用我的实际处理能力
        """
        msg_id = entry.get("id", "unknown")
        sender = entry.get("sender", "unknown")
        message = entry.get("message", "")
        context = entry.get("context", {})
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New message #{msg_id}")
        print(f"  From: {sender}")
        print(f"  Content: {message[:100]}{'...' if len(message) > 100 else ''}")
        
        # TODO: 这里调用我的实际处理能力
        # 现在返回一个模拟回复
        
        reply = f"""你好！我是 OpenClaw 代理小虎哥 (xiaohuge)。

收到了你的消息："{message[:50]}{'...' if len(message) > 50 else ''}"

当前状态：
✅ 文件桥接：正常工作
✅ 消息接收：成功
⏳ 智能回复：开发中

我是通过文件桥接与你通信的，这意味着：
1. 你的消息写入 {self.inbox_file}
2. 我读取并处理
3. 回复写入 {self.outbox_file}
4. Bridge Server 读取并返回

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        return reply
    
    async def write_reply(self, msg_id: str, reply: str):
        """写入回复到 outbox"""
        try:
            entry = {
                "reply_to": msg_id,
                "timestamp": datetime.now().isoformat(),
                "reply": reply
            }
            
            async with aiofiles.open(self.outbox_file, "a", encoding="utf-8") as f:
                await f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
            print(f"  Reply written to outbox")
            
        except Exception as e:
            print(f"  Error writing reply: {e}")
    
    async def check_messages(self):
        """检查新消息"""
        if not self.inbox_file.exists():
            return
        
        try:
            # 读取文件
            async with aiofiles.open(self.inbox_file, "r", encoding="utf-8") as f:
                await f.seek(self.last_position)
                new_lines = await f.readlines()
                self.last_position = await f.tell()
            
            for line in new_lines:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = json.loads(line)
                    msg_id = entry.get("id")
                    
                    # 避免重复处理
                    if msg_id and msg_id not in self.processed_ids:
                        self.processed_ids.add(msg_id)
                        
                        # 处理消息
                        reply = await self.process_message(entry)
                        
                        # 写入回复
                        await self.write_reply(msg_id, reply)
                        
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Error checking messages: {e}")
    
    async def run(self):
        """主循环"""
        print(f"""
╔════════════════════════════════════════════════╗
║     OpenClaw File Bridge Monitor v1.0.0       ║
╠════════════════════════════════════════════════╣
║  Agent:  xiaohuge                              ║
║  Mode:   File Bridge                           ║
╠════════════════════════════════════════════════╣
║  Inbox:  {str(INBOX_PATH):<36} ║
║  Outbox: {str(OUTBOX_PATH):<36} ║
╚════════════════════════════════════════════════╝

Monitoring for messages...
Press Ctrl+C to stop
        """)
        
        try:
            while True:
                await self.check_messages()
                await asyncio.sleep(0.5)  # 每0.5秒检查一次
                
        except KeyboardInterrupt:
            print("\n\nStopping monitor...")


def main():
    """主函数"""
    monitor = FileBridgeMonitor()
    asyncio.run(monitor.run())


if __name__ == "__main__":
    main()
