# IronSentinel 开发与运行指南

## 项目概述

IronSentinel v11.0 "Omni-Perception" 是一个开源、自治、高度透明的 AI 智能助理演化体。它具备全感知能力、自省机制和环境自愈能力的数字生命体雏形。

## 项目架构

```
wechatAGENT/
├── core/                   # 核心大脑与逻辑
│   ├── brain.py            # 自省中枢
│   ├── tool_manager.py     # 动态工具管理器
│   ├── agent.py            # LangChain Agent 集成
│   ├── config.py           # 配置管理
│   ├── env_init.py         # 环境初始化
│   └── tools/              # 核心演化与解码工具
├── kernel/                 # 内核级守门员
│   ├── bin/                # 存放 SILK/FFMPEG 二进制文件
│   ├── overseer.py         # 守护进程
│   └── privilege_guard.py  # 管理员提权逻辑
├── tools/                  # 业务工具库 (RPA, Search, Data...)
├── wechat/                 # 微信 UI 自动化监听与发送
├── worker/                 # 异步任务处理器
├── utils/                  # 稳定性、日志与自检工具
├── scheduler/              # 任务调度器
├── config/                 # 配置文件
├── data/                   # 数据存储
├── logs/                   # 日志文件
└── temp/                   # 临时文件
```

## 核心功能模块

### 1. 大脑模块 (core/brain.py)
- 动态生成系统提示词
- 维护 Agent 的自我意识
- 实时感知工具能力

### 2. 工具管理器 (core/tool_manager.py)
- 动态扫描并加载所有可用工具
- 生成能力说明字符串
- 支持工具自诊

### 3. 演化引擎 (tools/evolution.py)
- 代码修改与创建
- 语法自检
- 本地版本固化 (Git Commit)
- 热重启申请

### 4. 微信交互模块 (wechat/)
- 消息监听与发送
- 语音文件处理
- 微信窗口自动化

### 5. 内核守护 (kernel/)
- 权限提升
- 二进制组件管理
- 系统级监控

## 环境要求

### 系统要求
- Windows 10/11 (推荐)
- Python 3.10+
- Conda (推荐) 或 Python 虚拟环境
- Git

### 硬件要求
- 4GB+ RAM
- 2GB+ 可用磁盘空间
- 稳定的网络连接

## 快速开始

### 方法一：使用启动脚本 (推荐)
1. 双击运行 `start.bat`
2. 脚本会自动：
   - 检查并创建 Conda 环境
   - 安装依赖包
   - 创建 .env 配置文件
   - 启动主程序

### 方法二：手动安装
```bash
# 1. 创建虚拟环境
conda create -n wechat-ai python=3.10
conda activate wechat-ai

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
copy .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 4. 初始化环境
python tools/initialize_env.py

# 5. 启动程序
python main.py
```

## 配置说明

### 必需配置 (.env)
```env
# AI 供应商选择
LLM_PROVIDER=google  # 支持: google, openai, anthropic, deepseek
MODEL_NAME=gemini-2.0-flash

# API Keys (至少配置一个)
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 主人配置
MASTER_WXID=your_master_wxid_here
MASTER_REMARK=your_master_remark_here

# 微信白名单
WHITELIST=文件传输助手,张三,李四
```

### 可选配置
- `TAVILY_API_KEY`: 网页搜索 API
- `HTTPS_PROXY`/`HTTP_PROXY`: 代理设置
- `DB_PATH`: 数据库路径
- `LOG_LEVEL`: 日志级别

## 开发指南

### 添加新工具
1. 在 `tools/` 目录下创建新的 Python 文件
2. 使用 `@tool` 装饰器标记函数
3. 确保函数有清晰的文档字符串
4. 工具会自动被 `ToolManager` 扫描加载

示例：
```python
from langchain.tools import tool

@tool
def my_new_tool(param1: str, param2: int):
    """
    工具描述：这个工具用于...
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
        
    Returns:
        执行结果的描述
    """
    # 工具实现逻辑
    return f"执行结果: {param1} - {param2}"
```

### 修改核心逻辑
1. 使用 `evolve_code` 工具进行代码修改
2. 系统会自动进行语法检查
3. 修改会自动提交到 Git
4. 使用 `request_hot_reload` 应用更改

### 调试与日志
- 日志文件保存在 `logs/` 目录
- 支持不同日志级别：DEBUG, INFO, WARNING, ERROR
- 可以通过 `.env` 中的 `LOG_LEVEL` 配置

## 运行模式

### 1. 标准模式
```bash
python main.py
```
- 启动所有模块
- 监听微信消息
- 处理用户请求

### 2. 守护模式
```bash
python kernel/overseer.py
```
或
```bash
run_sentinel.bat
```
- 增强的监控和恢复机制
- 自动重启失败组件
- 系统级守护

### 3. 开发模式
```bash
# 启用调试日志
set LOG_LEVEL=DEBUG
python main.py
```

## 常见问题

### Q1: 启动时提示缺少 API Key
A: 检查 `.env` 文件是否已正确配置对应的 API Key。

### Q2: 微信消息无法接收
A: 
1. 确保微信客户端已登录
2. 检查白名单配置
3. 确认微信窗口未被最小化

### Q3: 语音功能无法使用
A:
1. 运行 `python tools/initialize_env.py` 初始化二进制组件
2. 检查 `kernel/bin/` 目录下是否有必要的可执行文件

### Q4: 代理配置问题
A:
1. 在 `.env` 中配置 `HTTPS_PROXY` 和 `HTTP_PROXY`
2. 确保代理地址和端口正确
3. 重启程序使配置生效

## 安全注意事项

### 禁止修改的文件
- `core/config_private.py` (如果存在)
- `.env` 文件中的敏感信息
- `data/` 目录下的数据库文件

### 权限管理
- 系统会自动请求管理员权限以访问受限资源
- 敏感操作需要二次确认
- 演化操作会被记录和审核

## 演化协议

IronSentinel 遵循透明演化闭环：
1. **汇报**: 接收指令后，通过 `report_evolution_progress` 同步计划
2. **编码**: 自主生成演化补丁
3. **重启**: 请求 `request_hot_reload`，系统重生后自动发送成功通知

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request
5. 确保代码符合项目规范

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 获取帮助

- 查看项目文档
- 提交 Issue
- 查看日志文件
- 联系项目维护者