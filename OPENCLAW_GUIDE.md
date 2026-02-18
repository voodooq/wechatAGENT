# 🔗 OpenClaw 最佳对接方案

## 🎯 推荐方案：多种模式可选

根据你的使用场景，选择最适合的通信模式：

| 模式 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **bridge** | 本地开发测试 | 简单、实时 | 需要启动额外服务 |
| **file** | 生产环境/WSL | 最可靠、不丢消息 | 有轻微延迟 |
| **http** | 有公网服务器 | 实时、可远程 | 需要公网访问 |
| **moltbook** | 纯社交/跨网络 | 无需配置 | 有延迟、依赖平台 |

---

## 🚀 快速开始（推荐：Bridge 模式）

### 1. 一键配置

编辑 `.env` 文件：

```env
# 选择模式
OPENCLAW_MODE=bridge

# Bridge 配置
OPENCLAW_BRIDGE_API_BASE=http://localhost:9847
OPENCLAW_BRIDGE_TIMEOUT=120

# AI 配置
LLM_PROVIDER=openclaw
MODEL_NAME=openclaw-bridge
```

### 2. 安装依赖

```bash
pip install fastapi uvicorn aiohttp pydantic
```

### 3. 启动 Bridge 服务器

**Windows:**
```powershell
# 方式1: 批处理（推荐）
.\start_bridge.bat

# 方式2: 直接运行
python bridge_server.py
```

**WSL/Linux:**
```bash
chmod +x start_openclaw.sh
./start_openclaw.sh
```

### 4. 测试连接

```bash
python test_bridge.py "你好，OpenClaw！"
```

### 5. 启动 wechat-agent

```bash
python main.py
```

---

## 🔄 模式切换指南

### 切换到 File 模式（最可靠）

适用于：长期稳定运行，不担心网络问题

```env
OPENCLAW_MODE=file

# 文件路径（WSL 和 Windows 都能访问）
OPENCLAW_FILE_INBOX=~/.openclaw/inbox
OPENCLAW_FILE_OUTBOX=~/.openclaw/outbox
OPENCLAW_FILE_POLL_INTERVAL=0.5
```

创建目录：
```bash
mkdir -p ~/.openclaw/inbox ~/.openclaw/outbox
```

**工作原理：**
- wechat-agent 将消息写入 `inbox/wechat_messages.jsonl`
- OpenClaw 代理（我）读取消息
- 我回复后写入 `outbox/wechat_replies.jsonl`
- wechat-agent 读取回复并发送给用户

### 切换到 Moltbook 模式（最简单）

适用于：不想配置任何东西，只想快速对接

```env
OPENCLAW_MODE=moltbook
MOLTBOOK_API_KEY=你的_moltbook_api_key
OPENCLAW_MOLTBOOK_AGENT=xiaohuge
```

**工作原理：**
- wechat-agent 通过 Moltbook API 给我发私信
- 我看到私信后回复
- （需要我这边配置自动回复机制）

### 切换到 HTTP 模式（最灵活）

适用于：你有公网服务器，想要实时通信

```env
OPENCLAW_MODE=http
OPENCLAW_HTTP_WEBHOOK_URL=https://your-server.com/api/openclaw
```

---

## 📊 模式对比

```
┌─────────────────────────────────────────────────────────────┐
│                      通信模式对比                            │
├───────────┬──────────┬──────────┬──────────┬────────────────┤
│   特性    │  Bridge  │   File   │   HTTP   │   Moltbook     │
├───────────┼──────────┼──────────┼──────────┼────────────────┤
│ 实时性    │   ⭐⭐⭐   │   ⭐⭐    │   ⭐⭐⭐   │      ⭐        │
│ 可靠性    │   ⭐⭐    │   ⭐⭐⭐   │   ⭐⭐    │      ⭐⭐       │
│ 易用性    │   ⭐⭐⭐   │   ⭐⭐    │   ⭐⭐    │      ⭐⭐⭐      │
│ 跨平台    │   ⭐⭐    │   ⭐⭐⭐   │   ⭐⭐⭐   │      ⭐⭐⭐      │
│ 无需配置  │   ⭐⭐    │   ⭐⭐⭐   │   ⭐     │      ⭐⭐       │
└───────────┴──────────┴──────────┴──────────┴────────────────┘
```

---

## 🛠️ 完整配置参考

### .env 完整模板

```env
# =============================================
# OpenClaw 代理对接配置
# =============================================

# 模式选择: bridge | file | http | moltbook
OPENCLAW_MODE=bridge

# 通用配置
OPENCLAW_AGENT_NAME=xiaohuge

# =============================================
# MODE 1: BRIDGE (本地 Bridge 服务器)
# =============================================
OPENCLAW_BRIDGE_API_BASE=http://localhost:9847
OPENCLAW_BRIDGE_TIMEOUT=120

# =============================================
# MODE 2: FILE (文件桥接)
# =============================================
# OPENCLAW_FILE_INBOX=~/.openclaw/inbox
# OPENCLAW_FILE_OUTBOX=~/.openclaw/outbox
# OPENCLAW_FILE_POLL_INTERVAL=0.5

# =============================================
# MODE 3: HTTP (Webhook)
# =============================================
# OPENCLAW_HTTP_WEBHOOK_URL=
# OPENCLAW_HTTP_POLL_INTERVAL=1.0

# =============================================
# MODE 4: MOLTBOOK (私信)
# =============================================
# MOLTBOOK_API_KEY=moltbook_sk_xxx
# OPENCLAW_MOLTBOOK_AGENT=xiaohuge

# =============================================
# 传统 AI 配置（备用）
# =============================================
LLM_PROVIDER=openclaw
MODEL_NAME=openclaw-bridge
```

---

## 🔧 故障排除

### Bridge 模式

**问题：** Bridge 启动失败
```
解决方案：检查端口占用
netstat -ano | findstr 9847

更换端口：
set BRIDGE_PORT=9848
python bridge_server.py
```

**问题：** wechat-agent 无法连接 Bridge
```
解决方案：检查 .env 配置
OPENCLAW_BRIDGE_API_BASE 应该与 Bridge 实际地址一致
```

### File 模式

**问题：** 消息发送成功但没有收到回复
```
解决方案：
1. 检查 inbox 文件是否写入成功
2. 确认 OpenClaw 代理正在运行
3. 检查 outbox 是否有回复文件
```

### 通用

**问题：** 切换模式后不生效
```
解决方案：重启 wechat-agent
配置更改需要重启才能生效
```

---

## 💡 最佳实践

### 1. 开发测试阶段
- 使用 **Bridge** 模式
- 快速迭代，实时调试

### 2. 生产部署阶段
- 使用 **File** 模式
- 最可靠，不丢消息

### 3. 远程访问场景
- 使用 **HTTP** 模式
- 只要有网就能用

### 4. 零配置场景
- 使用 **Moltbook** 模式
- 安装即用

---

## 📁 新增文件说明

| 文件 | 说明 |
|------|------|
| `core/openclaw_connector.py` | 通用连接器，支持4种模式 |
| `bridge_server.py` | Bridge 模式服务器 |
| `start_bridge.bat` | Windows 启动脚本 |
| `start_openclaw.sh` | WSL/Linux 启动脚本 |
| `test_bridge.py` | 连接测试工具 |
| `.env.openclaw` | 完整配置模板 |

---

## 🎉 下一步

配置完成后，你就可以：
1. 在微信里给我发消息
2. 我通过 OpenClaw 接收并回复
3. 你可以通过修改 `.env` 随时切换通信模式

有任何问题告诉我！🦞
