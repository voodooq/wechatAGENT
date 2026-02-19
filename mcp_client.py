"""
MCP 客户端工具集成

连接到 Tavily MCP 服务器，提供增强的搜索能力
"""
import os
import asyncio
from typing import Optional, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class TavilyMCPClient:
    """Tavily MCP 客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools: list = []
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, *args):
        await self.exit_stack.aclose()
    
    async def connect(self):
        """连接到 Tavily MCP 服务器"""
        if not self.api_key:
            raise ValueError("TAVILY_API_KEY 未设置")
        
        # Tavily MCP 服务器配置
        server_params = StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@tavily/mcp@latest",
                "--api-key",
                self.api_key
            ],
            env={**os.environ, "TAVILY_API_KEY": self.api_key}
        )
        
        # 连接到服务器
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        
        # 初始化会话
        await self.session.initialize()
        
        # 获取可用工具
        response = await self.session.list_tools()
        self.tools = response.tools
        
        print(f"✅ 已连接到 Tavily MCP 服务器")
        print(f"   可用工具: {[tool.name for tool in self.tools]}")
    
    async def search(self, query: str, **kwargs) -> str:
        """
        使用 Tavily MCP 工具搜索
        
        Args:
            query: 搜索查询
            **kwargs: 额外参数 (search_depth, max_results, etc.)
        """
        if not self.session:
            raise RuntimeError("MCP 会话未连接")
        
        # 构建参数
        arguments = {
            "query": query,
            **kwargs
        }
        
        # 调用 Tavily 搜索工具
        result = await self.session.call_tool(
            "tavily-search",
            arguments=arguments
        )
        
        # 提取文本内容
        content = "\n".join([
            item.text for item in result.content 
            if hasattr(item, 'text')
        ])
        
        return content
    
    async def extract(self, urls: list, **kwargs) -> str:
        """
        使用 Tavily MCP 工具提取网页内容
        
        Args:
            urls: URL 列表
            **kwargs: 额外参数
        """
        if not self.session:
            raise RuntimeError("MCP 会话未连接")
        
        arguments = {
            "urls": urls if isinstance(urls, list) else [urls],
            **kwargs
        }
        
        result = await self.session.call_tool(
            "tavily-extract",
            arguments=arguments
        )
        
        content = "\n".join([
            item.text for item in result.content 
            if hasattr(item, 'text')
        ])
        
        return content


# 便捷函数
async def tavily_mcp_search(query: str, api_key: Optional[str] = None) -> str:
    """使用 Tavily MCP 搜索（单次调用）"""
    async with TavilyMCPClient(api_key) as client:
        return await client.search(query)


if __name__ == "__main__":
    # 测试
    import sys
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print("请设置 TAVILY_API_KEY 环境变量")
        sys.exit(1)
    
    async def test():
        async with TavilyMCPClient(api_key) as client:
            result = await client.search("Python programming", max_results=3)
            print(result)
    
    asyncio.run(test())
