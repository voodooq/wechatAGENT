#!/usr/bin/env python3
"""
OpenClaw Bridge Worker - HTTP 桥接工作器

定期轮询 HTTP Bridge Server 获取微信消息，
处理完成后提交回复。

用法:
    设置环境变量后运行:
    export OPENCLAW_BRIDGE_URL=http://host.docker.internal:9848
    python openclaw_bridge_worker.py
"""

import os
import sys
import re
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path

# HTTP Bridge Server 地址
BRIDGE_URL = os.getenv("OPENCLAW_BRIDGE_URL", "http://host.docker.internal:9848")
POLL_INTERVAL = float(os.getenv("OPENCLAW_POLL_INTERVAL", "1.0"))  # 轮询间隔


class BridgeWorker:
    """HTTP Bridge 工作器"""
    
    def __init__(self):
        self.bridge_url = BRIDGE_URL
        self.session: aiohttp.ClientSession = None
        self.running = False
        self.stats = {
            "processed": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat()
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def get_pending_messages(self) -> list:
        """获取待处理的消息"""
        try:
            async with self.session.get(
                f"{self.bridge_url}/api/v1/messages",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("messages", [])
                return []
        except Exception as e:
            print(f"  ⚠️  获取消息失败: {e}")
            return []
    
    async def update_status(self, msg_id: str, status: str):
        """更新消息状态"""
        try:
            async with self.session.post(
                f"{self.bridge_url}/api/v1/messages/{msg_id}/status",
                params={"status": status},
                timeout=aiohttp.ClientTimeout(total=5)
            ):
                pass
        except:
            pass
    
    async def submit_reply(self, msg_id: str, reply: str) -> bool:
        """提交回复"""
        try:
            async with self.session.post(
                f"{self.bridge_url}/api/v1/reply",
                json={"msg_id": msg_id, "reply": reply},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"  ⚠️  提交回复失败: {e}")
            return False
    
    async def process_message(self, message: dict) -> str:
        """
        处理消息 - 使用 MCP Tavily 搜索和 Browser 工具
        
        支持:
        • MCP Tavily 搜索 (增强版)
        • 网页浏览 (Playwright)
        • 数据提取和分析
        """
        sender = message.get("sender", "unknown")
        content = message.get("message", "")
        
        print(f"  🧠 处理消息: {content[:50]}...")
        
        # 导入工具
        import sys
        sys.path.insert(0, '/home/node/openclaw/wechat-agent')
        
        # 检查是否需要搜索
        search_keywords = ["搜索", "查", "找", "是什么", "为什么", "怎么", "如何", "哪里", "多少", "价格", "时间", "天气", "新闻", "最新"]
        url_pattern = re.compile(r'https?://\S+')
        urls = url_pattern.findall(content)
        
        need_search = any(kw in content for kw in search_keywords) or bool(urls)
        
        if not need_search:
            # 简单对话回复
            content_lower = content.lower()
            if "你好" in content or "你是谁" in content:
                reply = f"""你好！我是小虎哥 (xiaohuge) 🦞

我是你的智能助手，可以帮助你：
• 使用 MCP Tavily 进行深度搜索
• 浏览网页和数据分析
• 协助各种日常任务

有什么我可以帮你的吗？"""
            elif "谢谢" in content:
                reply = "不客气！很高兴能帮到你。有其他问题随时找我 😊"
            else:
                reply = f"收到你的消息：{content}\n\n我在听，请继续说说你的需求。"
            
            if "🤖 AI 生成" not in reply:
                reply = f"{reply}\n\n---\n🤖 AI 生成"
            return reply
        
        # 需要搜索或浏览网页
        try:
            result_parts = []
            
            # 1. 如果有 URL，使用 Tavily Extract 或 Browser 工具
            if urls:
                print(f"  🌐 检测到 URL，提取内容...")
                
                # 尝试使用 MCP Tavily Extract
                try:
                    from mcp_client import TavilyMCPClient
                    async with TavilyMCPClient() as mcp:
                        for url in urls[:2]:
                            extract_result = await mcp.extract(url, include_images=False)
                            result_parts.append(f"【网页摘要】\n{extract_result[:1500]}")
                except Exception as e:
                    print(f"  ⚠️  Tavily Extract 失败，使用 Browser: {e}")
                    # 回退到 Browser 工具
                    for url in urls[:2]:
                        try:
                            from tools.browser_tool import browseWebpage
                            page_content = await browseWebpage(url)
                            result_parts.append(f"【网页内容】\n{page_content[:1500]}")
                        except Exception as be:
                            result_parts.append(f"【网页浏览失败】{url}: {str(be)}")
            
            # 2. 执行 MCP Tavily 搜索
            else:
                print(f"  🔍 使用 MCP Tavily 搜索: {content[:30]}...")
                try:
                    from mcp_client import TavilyMCPClient
                    
                    async with TavilyMCPClient() as mcp:
                        # 使用 MCP 进行深度搜索
                        search_result = await mcp.search(
                            content,
                            search_depth="advanced",
                            max_results=5
                        )
                        result_parts.append(f"【Tavily MCP 搜索结果】\n{search_result[:2000]}")
                        
                        # 尝试访问第一个结果获取更多信息
                        url_matches = re.findall(r'https?://[^\s\)]+', search_result)
                        if url_matches:
                            print(f"  🌐 提取首个结果详情...")
                            try:
                                extract_result = await mcp.extract(url_matches[0])
                                result_parts.append(f"\n【详细内容】\n{extract_result[:1500]}")
                            except:
                                pass
                            
                except Exception as e:
                    print(f"  ⚠️  MCP 搜索失败，使用传统搜索: {e}")
                    # 回退到传统搜索
                    try:
                        from tools.web_search_tool import searchWeb
                        search_results = await searchWeb(content)
                        result_parts.append(f"【搜索结果】\n{search_results[:1500]}")
                    except Exception as e2:
                        result_parts.append(f"【搜索失败】{str(e2)}")
            
            # 生成回复
            search_summary = "\n\n".join(result_parts)
            
            # 使用 AI 总结（简化版）
            reply = f"""根据您的询问 "{content[:50]}"，我通过 Tavily MCP 为您找到了以下信息：

{search_summary[:2800]}

💡 信息来源：Tavily MCP 搜索引擎
如果您需要更详细的信息或特定方面的分析，请告诉我！"""
            
        except Exception as e:
            print(f"  ⚠️  处理失败: {e}")
            import traceback
            traceback.print_exc()
            reply = f"抱歉，处理时发生错误: {str(e)[:80]}\n\n您可以尝试简化问题，或稍后再试。"
        
        # 确保有 AI 标记
        if "🤖 AI 生成" not in reply:
            reply = f"{reply}\n\n---\n🤖 AI 生成"
        
        return reply
    
    async def run(self):
        """主循环"""
        print(f"""
╔════════════════════════════════════════════════╗
║     OpenClaw Bridge Worker v1.0.0             ║
╠════════════════════════════════════════════════╣
║  Bridge URL: {self.bridge_url:<35} ║
║  Poll Interval: {POLL_INTERVAL}s{'':<30} ║
╚════════════════════════════════════════════════╝

🔄 开始轮询消息...
        """)
        
        self.running = True
        
        while self.running:
            try:
                # 获取待处理消息
                messages = await self.get_pending_messages()
                
                if messages:
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 发现 {len(messages)} 条新消息")
                    
                    for msg in messages:
                        msg_id = msg.get("id")
                        sender = msg.get("sender")
                        content = msg.get("message", "")[:50]
                        
                        print(f"  处理消息 #{msg_id} from {sender}: {content}...")
                        
                        # 更新状态为处理中
                        await self.update_status(msg_id, "processing")
                        
                        # 处理消息
                        try:
                            reply = await self.process_message(msg)
                            
                            # 提交回复
                            success = await self.submit_reply(msg_id, reply)
                            if success:
                                self.stats["processed"] += 1
                                print(f"  ✅ 消息 #{msg_id} 处理完成")
                            else:
                                self.stats["errors"] += 1
                                print(f"  ❌ 消息 #{msg_id} 提交失败")
                                
                        except Exception as e:
                            self.stats["errors"] += 1
                            print(f"  ❌ 消息 #{msg_id} 处理异常: {e}")
                            # 提交错误回复
                            await self.submit_reply(
                                msg_id, 
                                f"抱歉，处理时发生错误: {str(e)[:80]}\n\n---\n🤖 AI 生成"
                            )
                
                # 等待下一轮
                await asyncio.sleep(POLL_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n👋 收到停止信号")
                self.running = False
            except Exception as e:
                print(f"  ⚠️  主循环异常: {e}")
                await asyncio.sleep(5)
        
        print(f"\n📊 统计:")
        print(f"  处理消息: {self.stats['processed']}")
        print(f"  错误: {self.stats['errors']}")


async def main():
    async with BridgeWorker() as worker:
        await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 已停止")
