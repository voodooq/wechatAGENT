# MCP Tavily 配置指南

## 概述

已配置 **MCP (Model Context Protocol)** 连接到 Tavily 搜索引擎，提供更强大的搜索和网页提取能力。

## MCP 服务器信息

- **URL**: https://mcp.tavily.com/mcp/
- **API Key**: `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`
- **工具**:
  - `tavily-search`: 深度网页搜索
  - `tavily-extract`: 网页内容提取

## 配置文件

### 1. API Key 配置
文件: `.env.tavily`
```bash
export TAVILY_API_KEY=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
export TAVILY_MCP_URL=https://mcp.tavily.com/mcp/
```

### 2. MCP 客户端
文件: `mcp_client.py`
- `TavilyMCPClient` 类封装 MCP 连接
- 支持异步上下文管理器
- 自动安装和配置 Tavily MCP 服务器

## 启动步骤

### 1. 安装依赖
```bash
cd /home/node/openclaw/wechat-agent
pip install mcp -q
```

### 2. 测试 MCP 连接
```bash
source .env.tavily
python test_mcp.py
```

### 3. 启动 Worker
```bash
./start_worker.sh
```

## 使用方式

### 直接调用 MCP 客户端
```python
from mcp_client import TavilyMCPClient
import asyncio

async def search():
    async with TavilyMCPClient() as client:
        # 搜索
        result = await client.search("Python tutorials", max_results=5)
        print(result)
        
        # 提取网页
        extract = await client.extract("https://example.com")
        print(extract)

asyncio.run(search())
```

### 在 Worker 中自动使用
Worker 会自动检测消息类型：
- **搜索关键词** → 调用 `tavily-search`
- **URL 链接** → 调用 `tavily-extract` 或 `browseWebpage`

## 工作流程

```
用户消息: "搜索 Python 最佳实践"
    ↓
Worker 检测关键词 "搜索"
    ↓
连接 Tavily MCP 服务器 (通过 npx)
    ↓
调用 tavily-search 工具
    ↓
获取深度搜索结果
    ↓
生成汇总回复
```

## 依赖要求

| 依赖 | 用途 | 安装命令 |
|------|------|---------|
| mcp | MCP SDK | `pip install mcp` |
| npx | 运行 MCP 服务器 | Node.js 内置 |
| playwright | 浏览器工具 | `pip install playwright` |

## 故障排查

### 问题 1: npx 未找到
**解决**: 安装 Node.js
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
```

### 问题 2: MCP 连接失败
**解决**: 检查 API Key
```bash
echo $TAVILY_API_KEY
```

### 问题 3: Tavily Extract 失败
**解决**: 回退到 Browser 工具自动处理

## 优势

✅ **深度搜索**: Tavily 提供 AI 优化的搜索结果  
✅ **网页提取**: 自动提取网页正文内容  
✅ **结构化数据**: MCP 协议提供标准化接口  
✅ **自动重试**: 失败时自动回退到传统搜索  

## 文件清单

| 文件 | 说明 |
|------|------|
| `mcp_client.py` | MCP 客户端封装 |
| `.env.tavily` | API Key 配置 |
| `test_mcp.py` | 测试脚本 |
| `install_mcp.sh` | 安装脚本 |
