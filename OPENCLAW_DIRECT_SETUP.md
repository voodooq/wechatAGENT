# OpenClaw HTTP Bridge 直连配置指南

## 架构图

```
wechat-agent (Windows)
    ↓ HTTP POST /api/v1/chat
HTTP Bridge Server (端口 9848)
    ↓ 消息存入队列
    ↓ OpenClaw 轮询 /api/v1/messages
OpenClaw (Docker)
    ↓ 处理消息
    ↓ POST /api/v1/reply
HTTP Bridge Server
    ↓ 返回回复
wechat-agent
```

## 配置步骤

### 1. 确保 .env 配置正确

文件: `E:\work\wechatAGENT\.env`

```bash
# === OpenClaw 配置 ===
OPENCLAW_ENABLED=True
OPENCLAW_MODE=http
OPENCLAW_HTTP_API=http://localhost:9848

# === 其他配置保持不变 ===
LLM_PROVIDER=openclaw
MODEL_NAME=openclaw-bridge
WHITELIST=文件传输助手
```

### 2. 启动 HTTP Bridge Server

双击运行或命令行:
```bash
cd E:\work\wechatAGENT
start_http_bridge_openclaw.bat
```

或者手动:
```bash
python http_bridge_server.py
```

你应该看到:
```
╔════════════════════════════════════════════════╗
║     OpenClaw HTTP Bridge Server v3.0.0        ║
╠════════════════════════════════════════════════╣
║  Mode:   OpenClaw Direct Connection            ║
╚════════════════════════════════════════════════╝
```

### 3. 启动 OpenClaw Bridge Worker (Docker 内)

在 OpenClaw Docker 容器内运行:

```bash
# 设置环境变量
export OPENCLAW_BRIDGE_URL=http://host.docker.internal:9848

# 启动工作器
python /home/node/openclaw/wechat-agent/openclaw_bridge_worker.py
```

或者创建启动脚本:

```bash
cat > /home/node/openclaw/start_bridge_worker.sh << 'EOF'
#!/bin/bash
cd /home/node/openclaw/wechat-agent
export OPENCLAW_BRIDGE_URL=http://host.docker.internal:9848
export OPENCLAW_POLL_INTERVAL=1.0
python openclaw_bridge_worker.py
EOF
chmod +x /home/node/openclaw/start_bridge_worker.sh
```

### 4. 启动 IronSentinel

```bash
run_sentinel.bat
```

## 测试连接

### 测试 Bridge Server
```bash
curl http://localhost:9848/health
```

### 从 OpenClaw 端测试
```bash
curl http://host.docker.internal:9848/health
```

## 故障排查

### 问题 1: OpenClaw 无法连接 Bridge Server

**症状**: `Connection refused` 或 `Connection timeout`

**解决**:
1. 确认 Bridge Server 已启动 (端口 9848)
2. 在 Docker 内使用 `host.docker.internal` 访问主机
3. 检查防火墙是否阻挡端口 9848

### 问题 2: 消息没有回复

**症状**: 消息发送后一直等待

**解决**:
1. 确认 OpenClaw Bridge Worker 已启动
2. 检查 Worker 日志是否有处理消息
3. 确认 `OPENCLAW_BRIDGE_URL` 设置正确

### 问题 3: 回复超时

**症状**: 返回 "响应超时"

**解决**:
1. 检查 OpenClaw 处理时间是否过长
2. 调整 `http_bridge_server.py` 中的 `max_wait` 时间
3. 检查是否有错误导致 Worker 卡住

## 端口说明

| 服务 | 端口 | 说明 |
|------|------|------|
| HTTP Bridge Server | 9848 | 接收 wechat-agent 消息 |
| OpenClaw Gateway | 3333 | OpenClaw 主服务 |

## 文件清单

| 文件 | 说明 |
|------|------|
| `http_bridge_server.py` | HTTP Bridge 服务器 (v3.0) |
| `openclaw_bridge_worker.py` | OpenClaw 工作器 |
| `start_http_bridge_openclaw.bat` | Windows 启动脚本 |

## 优势

✅ **实时性好**: HTTP 通信比文件更快  
✅ **架构清晰**: Bridge 只负责消息转发  
✅ **易于调试**: 每个组件职责单一  
✅ **可扩展**: 可以轻松添加消息队列持久化  
