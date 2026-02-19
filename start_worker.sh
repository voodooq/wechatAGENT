#!/bin/bash
# OpenClaw Bridge Worker 启动脚本 (Docker 内部使用)
# 用法: ./start_worker.sh

cd /home/node/openclaw/wechat-agent

# 加载 Tavily MCP 配置
source .env.tavily 2>/dev/null || echo "⚠️  Tavily 配置未加载"

# 配置环境变量
export OPENCLAW_BRIDGE_URL=http://host.docker.internal:9848
export OPENCLAW_POLL_INTERVAL=1.0

echo "============================================"
echo "  OpenClaw Bridge Worker"
echo "  版本: 1.0.0"
echo "============================================"
echo ""
echo "📡 连接信息:"
echo "   Bridge URL: $OPENCLAW_BRIDGE_URL"
echo "   轮询间隔: $OPENCLAW_POLL_INTERVAL 秒"
echo ""
echo "🚀 正在启动 Worker..."
echo "   (按 Ctrl+C 停止)"
echo ""

# 检查依赖
python3 -c "import aiohttp" 2>/dev/null || {
    echo "⚠️  缺少 aiohttp，正在安装..."
    pip install aiohttp -q
}

python3 -c "import playwright" 2>/dev/null || {
    echo "⚠️  缺少 playwright，正在安装..."
    pip install playwright -q
    echo "📦 安装 Chromium 浏览器..."
    playwright install chromium
}

python3 -c "import html2text" 2>/dev/null || {
    echo "⚠️  缺少 html2text，正在安装..."
    pip install html2text -q
}

python3 -c "import mcp" 2>/dev/null || {
    echo "⚠️  缺少 MCP SDK，正在安装..."
    pip install mcp -q
}

# 检查 Node.js (MCP 服务器需要)
which npx >/dev/null 2>&1 || {
    echo "⚠️  警告: npx 未找到，MCP 服务器可能无法启动"
    echo "   请安装 Node.js: https://nodejs.org/"
}

# 启动 Worker
exec python3 openclaw_bridge_worker.py
