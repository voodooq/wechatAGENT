# 🔧 OpenClaw 模式配置指南

## 端口说明

| 模式 | 端口 | 启动文件 | 特点 |
|------|------|----------|------|
| **bridge** | 9847 | `bridge_server.py` | 文件桥接，最可靠 |
| **http** | 9848 | `http_bridge_server.py` | HTTP通信，最快 |

## 当前配置

你的 `.env` 设置：
```env
OPENCLAW_MODE=http
OPENCLAW_HTTP_API=http://localhost:9848
```

这意味着使用 **HTTP 模式 (端口 9848)**

## 启动步骤

### HTTP 模式（当前配置）

**1. 启动 HTTP Bridge Server（窗口1）**
```powershell
cd E:\work\wechatAGENT
python http_bridge_server.py
```
或双击 `start_http_bridge.bat`

**2. 启动 wechat-agent（窗口2）**
```powershell
cd E:\work\wechatAGENT
python main.py
```

### Bridge 模式（备选）

如果你想切换回 Bridge 模式：

**修改 `.env`：**
```env
OPENCLAW_MODE=bridge
OPENCLAW_BRIDGE_API_BASE=http://localhost:9847
```

**启动 Bridge Server：**
```powershell
python bridge_server.py
```

## 常见问题

### 错误：None/api/v1/chat

**原因**：HTTP 服务器没启动，或配置错误

**解决**：
1. 确保 `http_bridge_server.py` 正在运行
2. 检查 `.env` 中的 `OPENCLAW_HTTP_API` 是否匹配

### 端口冲突

如果 9848 被占用：
```powershell
# 修改 http_bridge_server.py 中的端口
# 或设置环境变量
set HTTP_BRIDGE_PORT=9849
```

## 推荐配置

**追求速度**：使用 HTTP 模式 (端口 9848)
**追求稳定**：使用 Bridge 模式 (端口 9847)

现在你的配置是 HTTP 模式，请确保启动 `http_bridge_server.py`！
