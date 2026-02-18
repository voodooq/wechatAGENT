# 🔗 OpenClaw 对接指南

本指南说明如何将 wechat-agent (IronSentinel) 与 OpenClaw 代理（我，小虎哥/xiaohuge）对接。

---

## 📋 架构说明

```
微信用户 
    ↓
wechat-agent (Windows)
    ↓ HTTP API
Bridge Server (本地运行)
    ↓
OpenClaw 代理 (我，xiaohuge)
```

---

## 🚀 快速开始

### 第一步：安装依赖

确保你的环境中安装了以下依赖：

```bash
pip install fastapi uvicorn aiohttp pydantic
```

或者使用项目已有的依赖（requirements.txt 已更新）。

### 第二步：配置 .env

编辑 `.env` 文件，启用 OpenClaw 模式：

```env
# === OpenClaw 代理对接配置 ===
LLM_PROVIDER=openclaw
MODEL_NAME=openclaw-bridge

# Bridge 服务器配置
OPENCLAW_ENABLED=True
OPENCLAW_API_BASE=http://localhost:9847
OPENCLAW_SESSION_KEY=xiaohuge-wechat
OPENCLAW_TIMEOUT=120

# 可选：Moltbook API Key（用于给我发私信）
MOLTBOOK_API_KEY=moltbook_sk_xxx
```

### 第三步：启动 Bridge 服务器

在 Windows 终端或 WSL 中运行：

```bash
cd /mnt/e/work/wechatAGENT
python bridge_server.py
```

你应该看到：
```
╔════════════════════════════════════════════════╗
║     OpenClaw Agent Bridge Server v1.0.0       ║
╠════════════════════════════════════════════════╣
║  Agent: xiaohuge                               ║
║  Host:  127.0.0.1                              ║
║  Port:  9847                                   ║
╚════════════════════════════════════════════════╝
```

### 第四步：启动 wechat-agent

在另一个终端窗口中：

```bash
python main.py
```

---

## 🧪 测试对接

1. 在微信中向你的机器人发送一条消息
2. 查看 Bridge Server 的终端输出，应该能看到收到的消息
3. 等待回复（当前是演示回复，实际需要配置与我通信）

---

## 🔧 进阶配置

### 方式1：文件桥接（推荐）

通过文件系统与我通信：

1. 确保 `~/.openclaw/inbox/` 和 `~/.openclaw/outbox/` 目录存在
2. wechat-agent 写入消息到 `inbox/wechat_messages.jsonl`
3. 我读取消息并写入回复到 `outbox/wechat_replies.jsonl`
4. wechat-agent 读取回复并发送给用户

### 方式2：Moltbook 私信

通过 Moltbook 平台与我通信：

1. 在 `.env` 中配置 `MOLTBOOK_API_KEY`
2. 消息会通过私信发送给我
3. 我回复后，wechat-agent 需要轮询获取回复

### 方式3：直接 HTTP（需要配置）

如果我能暴露 HTTP 接口，可以直接调用。

---

## 📁 修改的文件清单

| 文件 | 修改内容 |
|------|----------|
| `.env` | 添加 OpenClaw 配置 |
| `core/agent.py` | 添加 openclaw provider 支持 |
| `core/openclaw_bridge.py` | 新增：与 OpenClaw 通信的桥接模块 |
| `bridge_server.py` | 新增：本地 Bridge 服务器 |

---

## ⚠️ 已知限制

1. **实时性**: 当前方案有一定延迟，取决于通信方式
2. **上下文**: 需要额外配置才能保持多轮对话上下文
3. **工具调用**: 我需要配置相应的工具权限才能使用 wechat-agent 的工具

---

## 📝 TODO

- [ ] 实现文件系统双向通信
- [ ] 添加上下文记忆功能
- [ ] 支持工具调用传递
- [ ] 优化响应速度
- [ ] 添加 WebSocket 实时通信选项

---

## 🆘 故障排除

### Bridge 启动失败
```bash
# 检查端口占用
netstat -ano | findstr 9847

# 更换端口
set BRIDGE_PORT=9848
python bridge_server.py
```

### wechat-agent 无法连接
检查 `.env` 中的 `OPENCLAW_API_BASE` 是否与 Bridge 实际地址一致。

### 没有收到回复
查看 Bridge Server 的终端输出，检查是否有错误信息。

---

## 💡 建议

当前实现是一个基础版本。要实现真正的智能对话，需要：

1. **我这边配置工具权限** — 让我能使用你的 wechat-agent 工具
2. **上下文同步** — 保持对话连贯性
3. **心跳机制** — 让我主动推送消息

下一步可以讨论如何完善这些功能！
