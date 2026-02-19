#!/bin/bash
# OpenClaw Docker 服务启动脚本 (在 WSL 中运行)
# 
# 用途: 一键启动 HTTP Bridge + Bridge Worker
# 位置: 在 WSL 中运行此脚本

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════╗"
echo "║     OpenClaw Docker 服务管理器              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 检查是否在 WSL 中
if [[ ! -f /proc/version ]] || ! grep -q "microsoft" /proc/version 2>/dev/null; then
    echo "⚠️  警告: 此脚本建议在 WSL 中运行"
    echo ""
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    echo "   请先安装 Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

# 使用正确的 docker compose 命令
if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# 功能选择
case "${1:-start}" in
    start)
        echo "🚀 启动 OpenClaw Docker 服务..."
        echo ""
        echo "服务列表:"
        echo "  1. HTTP Bridge Server (端口 9848)"
        echo "  2. Bridge Worker (MCP Tavily + Browser)"
        echo ""
        
        # 检查 E 盘挂载
        if [[ ! -d /mnt/e/work/wechatAGENT ]]; then
            echo "⚠️  警告: /mnt/e/work/wechatAGENT 目录不存在"
            echo "   请确保 E 盘已挂载到 WSL:"
            echo "   sudo mkdir -p /mnt/e && sudo mount -t drvfs E: /mnt/e"
            echo ""
        fi
        
        # 创建缓存目录
        mkdir -p /home/node/.openclaw
        
        # 启动服务
        $COMPOSE_CMD -f docker-compose.yml up -d --build
        
        echo ""
        echo "✅ 服务已启动!"
        echo ""
        echo "📊 查看状态:"
        echo "   $0 status"
        echo ""
        echo "📜 查看日志:"
        echo "   $0 logs"
        echo ""
        echo "🔗 访问地址:"
        echo "   HTTP Bridge: http://localhost:9848"
        echo "   Health Check: http://localhost:9848/health"
        echo ""
        echo "💡 Windows 连接地址:"
        echo "   http://host.docker.internal:9848"
        ;;
    
    stop)
        echo "🛑 停止 OpenClaw Docker 服务..."
        $COMPOSE_CMD -f docker-compose.yml down
        echo "✅ 服务已停止"
        ;;
    
    restart)
        echo "🔄 重启 OpenClaw Docker 服务..."
        $COMPOSE_CMD -f docker-compose.yml restart
        echo "✅ 服务已重启"
        ;;
    
    status)
        echo "📊 服务状态:"
        $COMPOSE_CMD -f docker-compose.yml ps
        echo ""
        echo "🌐 网络连接测试:"
        curl -s http://localhost:9848/health 2>/dev/null | head -20 || echo "   ❌ Bridge 未响应"
        ;;
    
    logs)
        echo "📜 服务日志:"
        $COMPOSE_CMD -f docker-compose.yml logs -f
        ;;
    
    logs-bridge)
        echo "📜 HTTP Bridge 日志:"
        $COMPOSE_CMD -f docker-compose.yml logs -f http-bridge
        ;;
    
    logs-worker)
        echo "📜 Bridge Worker 日志:"
        $COMPOSE_CMD -f docker-compose.yml logs -f bridge-worker
        ;;
    
    update)
        echo "🔄 更新并重启服务..."
        $COMPOSE_CMD -f docker-compose.yml pull
        $COMPOSE_CMD -f docker-compose.yml up -d --build
        echo "✅ 服务已更新"
        ;;
    
    shell-bridge)
        echo "🔧 进入 HTTP Bridge 容器..."
        docker exec -it openclaw-http-bridge bash
        ;;
    
    shell-worker)
        echo "🔧 进入 Bridge Worker 容器..."
        docker exec -it openclaw-bridge-worker bash
        ;;
    
    test)
        echo "🧪 测试服务..."
        echo ""
        echo "1. 测试 Bridge Server:"
        curl -s http://localhost:9848/health 2>/dev/null | head -20 || echo "   ❌ Bridge 未响应"
        echo ""
        echo "2. 查看 Worker 状态:"
        docker logs openclaw-bridge-worker --tail 20 2>/dev/null || echo "   Worker 日志不可用"
        ;;
    
    *)
        echo "用法: $0 [命令]"
        echo ""
        echo "命令:"
        echo "  start          启动服务 (默认)"
        echo "  stop           停止服务"
        echo "  restart        重启服务"
        echo "  status         查看状态"
        echo "  logs           查看所有日志"
        echo "  logs-bridge    查看 Bridge 日志"
        echo "  logs-worker    查看 Worker 日志"
        echo "  update         更新并重启"
        echo "  shell-bridge   进入 Bridge 容器"
        echo "  shell-worker   进入 Worker 容器"
        echo "  test           测试服务"
        echo ""
        ;;
esac
