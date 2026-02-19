#!/bin/bash
# OpenClaw Docker 一键启动脚本
# 在 WSL 中运行此脚本

echo "🚀 OpenClaw Docker 一键启动"
echo ""

# 进入目录
cd /mnt/e/work/wechatAGENT || {
    echo "❌ 错误: 无法进入 /mnt/e/work/wechatAGENT"
    echo "   请确保 E 盘已挂载到 WSL"
    exit 1
}

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

# 确保脚本可执行
chmod +x docker-manage.sh 2>/dev/null

# 启动服务
echo "📦 正在启动 Docker 服务..."
echo "   - HTTP Bridge Server (端口 9848)"
echo "   - Bridge Worker (MCP + Browser)"
echo ""

./docker-manage.sh start

echo ""
echo "✅ 启动完成!"
echo ""
echo "🔍 查看状态: ./docker-manage.sh status"
echo "📜 查看日志: ./docker-manage.sh logs"
echo ""
echo "💡 Windows 配置:"
echo "   1. 运行: update-windows-config.bat"
echo "   2. 启动: run_sentinel.bat"
echo ""
