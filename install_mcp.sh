#!/bin/bash
# MCP 客户端安装脚本

echo "📦 安装 MCP 客户端..."

# 安装 mcp Python SDK
pip install mcp -q

# 检查安装
python3 -c "import mcp; print(f'MCP version: {mcp.__version__}')" 2>/dev/null || {
    echo "⚠️  安装失败，尝试从 GitHub 安装..."
    pip install git+https://github.com/modelcontextprotocol/python-sdk.git -q
}

echo "✅ MCP 客户端安装完成"
