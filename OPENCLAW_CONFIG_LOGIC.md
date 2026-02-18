# ⚙️ OpenClaw 配置逻辑说明

## 🔑 核心配置

### 总开关（最高优先级）

```env
OPENCLAW_ENABLED=True
```

当设置为 `True` 时：
- ✅ 强制启用 OpenClaw 模式
- ❌ 传统 AI 配置完全不会生效
- 🔒 即使 OpenClaw 连接失败，也不会回退到传统 AI

当设置为 `False` 或未设置时：
- 根据 `LLM_PROVIDER` 决定使用 OpenClaw 还是传统 AI

---

## 📊 配置组合表

| OPENCLAW_ENABLED | LLM_PROVIDER | 结果 |
|------------------|--------------|------|
| `True` | `openclaw` | ✅ 纯 OpenClaw 模式 |
| `True` | `google/openai/...` | ✅ 强制 OpenClaw，忽略传统配置 |
| `False` | `openclaw` | ✅ OpenClaw 模式 |
| `False` | `google` | ✅ 传统 Google AI 模式 |
| 未设置 | `openclaw` | ✅ OpenClaw 模式 |
| 未设置 | `google` | ✅ 传统 Google AI 模式 |

---

## 🎯 使用场景

### 场景 1：完全使用 OpenClaw（推荐）
```env
OPENCLAW_ENABLED=True
OPENCLAW_MODE=bridge
```
- 传统 AI 完全不加载
- 启动更快（不初始化 LangChain 模型）
- 如果 OpenClaw 连接失败，返回错误信息

### 场景 2：优先 OpenClaw，失败时降级
```env
OPENCLAW_ENABLED=False
LLM_PROVIDER=openclaw
```
- 首先尝试 OpenClaw
- 如果失败，自动回退到 `LLM_PROVIDER` 指定的传统 AI

### 场景 3：传统 AI 模式
```env
# 不设置 OPENCLAW_ENABLED
# 或
OPENCLAW_ENABLED=False
LLM_PROVIDER=google
```
- 完全使用传统 AI
- OpenClaw 相关代码不执行

---

## ⚠️ 重要说明

### 当 `OPENCLAW_ENABLED=True` 时：

以下配置会被**完全忽略**：
```env
LLM_PROVIDER=...        # 忽略
MODEL_NAME=...          # 忽略
GOOGLE_API_KEY=...      # 忽略
OPENAI_API_KEY=...      # 忽略
DEEPSEEK_API_KEY=...    # 忽略
# ... 所有传统 AI 配置
```

### 启动日志提示

开启 OpenClaw 后，你会看到：
```
[OpenClaw] Processing message from xxx (mode: openclaw)
[OpenClawConnector] Mode: bridge
```

---

## 🔧 快速切换

### 切换到纯 OpenClaw：
```env
OPENCLAW_ENABLED=True
OPENCLAW_MODE=bridge
```

### 切换到传统 AI：
```env
OPENCLAW_ENABLED=False
LLM_PROVIDER=deepseek
MODEL_NAME=deepseek-chat
```

### 临时禁用 OpenClaw：
```env
# 注释掉或设为 False
# OPENCLAW_ENABLED=False
```

---

## 🐛 故障排除

### 问题：设置了 OpenClaw 但还在用传统 AI

**检查 1：** `.env` 文件是否保存
```bash
# 在 wechat-agent 目录下
cat .env | grep OPENCLAW_ENABLED
```

**检查 2：** 是否重启了 wechat-agent
```bash
# 配置更改需要重启生效
python main.py
```

**检查 3：** 查看启动日志
```
# 应该看到
[OpenClaw] Processing message from xxx
```

### 问题：OpenClaw 连接失败

**情况 1：** Bridge 服务器未启动
```bash
# 启动 Bridge
python bridge_server.py
```

**情况 2：** 端口冲突
```bash
# 修改端口
OPENCLAW_BRIDGE_API_BASE=http://localhost:9848
```

**情况 3：** 配置错误
```bash
# 检查配置
cat .env | grep OPENCLAW
```

---

## 💡 最佳实践

1. **开发阶段**：使用 `OPENCLAW_ENABLED=False`，方便切换对比
2. **生产环境**：使用 `OPENCLAW_ENABLED=True`，确保稳定性
3. **备份配置**：保留传统 AI 配置作为应急方案
4. **监控日志**：关注 `[OpenClaw]` 开头的日志信息

---

有任何问题随时问我！🦞
