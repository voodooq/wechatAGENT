#!/bin/bash
# =============================================
# OpenClaw 连接器启动脚本 (WSL/Linux)
# =============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "  OpenClaw Agent Connector"
echo "========================================="
echo ""

# 获取当前模式
MODE=${OPENCLAW_MODE:-bridge}
echo "当前模式: $MODE"
echo ""

case $MODE in
    bridge)
        echo -e "${GREEN}[模式: Bridge]${NC} 启动本地 Bridge 服务器..."
        echo "请确保 Python 依赖已安装:"
        echo "  pip install fastapi uvicorn aiohttp"
        echo ""
        python bridge_server.py
        ;;
        
    file)
        echo -e "${GREEN}[模式: File]${NC} 文件桥接模式"
        echo "此模式下："
        echo "  - wechat-agent 写入消息到 inbox"
        echo "  - OpenClaw 代理读取并回复到 outbox"
        echo ""
        echo "请确保目录存在:"
        echo "  mkdir -p ~/.openclaw/inbox ~/.openclaw/outbox"
        echo ""
        echo "OpenClaw 代理需要独立运行文件监听器"
        ;;
        
    http)
        echo -e "${GREEN}[模式: HTTP]${NC} Webhook 模式"
        echo "请确保已配置:"
        echo "  OPENCLAW_HTTP_WEBHOOK_URL"
        echo ""
        ;;
        
    moltbook)
        echo -e "${GREEN}[模式: Moltbook]${NC} 私信模式"
        echo "请确保已配置:"
        echo "  MOLTBOOK_API_KEY"
        echo ""
        ;;
        
    *)
        echo -e "${RED}[错误]${NC} 未知的 OPENCLAW_MODE: $MODE"
        echo "支持的模式: bridge, file, http, moltbook"
        exit 1
        ;;
esac
