# OpenClaw Docker 部署指南 (WSL)

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Windows 主机                            │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │   IronSentinel       │      │   WeChat 客户端      │    │
│  │   (run_sentinel.bat) │      │                      │    │
│  └──────────┬───────────┘      └──────────────────────┘    │
│             │                                                │
│             │ HTTP POST http://host.docker.internal:9848    │
│             │                                                │
│  ╔══════════╧════════════════════════════════════════════╗  │
│  ║                    WSL 2 / Docker                      ║  │
│  ║  ┌─────────────────────────────┐                      ║  │
│  ║  │   HTTP Bridge Server        │  端口: 9848          ║  │
│  ║  │   (docker-compose.yml)      │  暴露: 主机 9848     ║  │
│  ║  └───────────┬─────────────────┘                      ║  │
│  ║              │ HTTP (内部网络)                         ║  │
│  ║  ┌───────────┴─────────────────┐                      ║  │
│  ║  │   Bridge Worker             │                      ║  │
│  ║  │   - MCP Tavily 搜索         │                      ║  │
│  ║  │   - Playwright 浏览器       │                      ║  │
│  ║  │   - 消息处理                │                      ║  │
│  ║  └─────────────────────────────┘                      ║  │
│  ╚═══════════════════════════════════════════════════════╝  │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 在 WSL 中启动 Docker 服务

```bash
# 进入目录
cd /mnt/e/work/wechatAGENT

# 一键启动
./docker-manage.sh start
```

### 2. 在 Windows 中更新配置

双击运行:
```
update-windows-config.bat
```

### 3. 启动 IronSentinel

```bash
run_sentinel.bat
```

## 详细步骤

### 第一步: 确保 WSL 和 Docker 就绪

```bash
# 检查 WSL
wsl --status

# 检查 Docker
wsl docker --version

# 确保 E 盘挂载
ls /mnt/e/work/wechatAGENT
```

### 第二步: 启动 Docker 服务

在 **WSL 终端** 中运行:

```bash
cd /mnt/e/work/wechatAGENT

# 添加执行权限
chmod +x docker-manage.sh

# 启动服务
./docker-manage.sh start
```

首次启动会:
1. 下载 node:22 Docker 镜像
2. 安装 Python 依赖 (aiohttp, playwright, mcp)
3. 安装 Chromium 浏览器
4. 启动 HTTP Bridge Server
5. 启动 Bridge Worker

### 第三步: 验证服务

```bash
# 查看状态
./docker-manage.sh status

# 测试连接
curl http://localhost:9848/health

# 查看日志
./docker-manage.sh logs
```

### 第四步: 配置 Windows 端

在 **Windows PowerShell/CMD** 中:

```powershell
# 更新 .env 配置
.\update-windows-config.bat

# 或手动编辑 .env，确保:
# OPENCLAW_MODE=http
# OPENCLAW_HTTP_API=http://host.docker.internal:9848
```

### 第五步: 启动 IronSentinel

```bash
run_sentinel.bat
```

## 管理命令

### 在 WSL 中管理

```bash
# 查看所有命令
./docker-manage.sh

# 启动服务
./docker-manage.sh start

# 停止服务
./docker-manage.sh stop

# 重启服务
./docker-manage.sh restart

# 查看状态
./docker-manage.sh status

# 查看日志
./docker-manage.sh logs              # 所有服务
./docker-manage.sh logs-bridge       # 仅 Bridge
./docker-manage.sh logs-worker       # 仅 Worker

# 进入容器调试
./docker-manage.sh shell-bridge      # 进入 Bridge 容器
./docker-manage.sh shell-worker      # 进入 Worker 容器

# 测试服务
./docker-manage.sh test
```

### Docker Compose 命令

```bash
# 查看运行中的容器
docker compose ps

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f
```

## 配置 Systemd 自动启动 (可选)

```bash
# 复制服务文件
sudo cp openclaw-worker.service /etc/systemd/system/

# 重新加载配置
sudo systemctl daemon-reload

# 启用自动启动
sudo systemctl enable openclaw-worker

# 启动服务
sudo systemctl start openclaw-worker

# 查看状态
sudo systemctl status openclaw-worker
```

## 文件说明

| 文件 | 位置 | 用途 |
|------|------|------|
| `docker-compose.yml` | WSL/E盘 | Docker 服务定义 |
| `docker-manage.sh` | WSL/E盘 | 管理脚本 |
| `update-windows-config.bat` | Windows/E盘 | Windows 配置更新 |
| `openclaw-worker.service` | WSL | Systemd 服务文件 |

## 网络配置

### Docker 网络
- **HTTP Bridge**: 监听 `0.0.0.0:9848`
- **Worker**: 内部连接 `http://http-bridge:9848`

### Windows 连接
- **地址**: `http://host.docker.internal:9848`
- **原理**: Docker Desktop 自动映射到 WSL2 虚拟机

### WSL 本地连接
- **地址**: `http://localhost:9848` 或 `http://127.0.0.1:9848`

## 故障排查

### 问题 1: E 盘未挂载

**症状**: `/mnt/e/work/wechatAGENT` 不存在

**解决**:
```bash
# 手动挂载
sudo mkdir -p /mnt/e
sudo mount -t drvfs E: /mnt/e

# 或配置自动挂载
# 编辑 /etc/wsl.conf
[automount]
enabled = true
mountFsTab = true
root = /mnt/
```

### 问题 2: Docker 未启动

**症状**: `Cannot connect to the Docker daemon`

**解决**:
```bash
# 启动 Docker 服务
sudo service docker start
# 或
sudo systemctl start docker
```

### 问题 3: 端口被占用

**症状**: `bind: address already in use`

**解决**:
```bash
# 查找占用 9848 的进程
sudo lsof -i :9848
# 或
sudo netstat -tulpn | grep 9848

# 停止占用进程
sudo kill -9 <PID>
```

### 问题 4: Windows 无法连接

**症状**: `curl http://host.docker.internal:9848` 超时

**解决**:
1. 确保 Docker Desktop 中启用了 WSL2 集成
2. 检查防火墙设置
3. 尝试使用 WSL IP:
   ```bash
   # 获取 WSL IP
   ip addr show eth0 | grep 'inet\b' | awk '{print $2}' | cut -d/ -f1
   ```

### 问题 5: Worker 无法连接 Bridge

**症状**: Worker 日志显示连接失败

**解决**:
```bash
# 查看 Bridge 是否健康
./docker-manage.sh test

# 重启服务
./docker-manage.sh restart
```

## 性能优化

### 资源限制
在 `docker-compose.yml` 中:
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
```

### 缓存持久化
已配置的缓存卷:
- `openclaw-pip-cache`: Python 包缓存
- `openclaw-node-modules`: Node 模块缓存

### 日志管理
日志自动轮转:
- 最大 100MB
- 保留 3 个文件

## 更新部署

```bash
# 更新代码后重启
cd /mnt/e/work/wechatAGENT
git pull  # 或手动更新
./docker-manage.sh update
```

## 安全提示

⚠️ **API Key 已写入配置文件**:
- `.env.tavily` 包含 Tavily API Key
- 请勿提交到 Git
- 已添加到 `.gitignore`

## 参考

- [Docker Compose 文档](https://docs.docker.com/compose/)
- [WSL 网络配置](https://docs.microsoft.com/en-us/windows/wsl/networking)
- [Tavily MCP](https://docs.tavily.com/)
