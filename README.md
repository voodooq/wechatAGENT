# 🤖 IronSentinel v11.0 "Omni-Perception"

[![Project Version](https://img.shields.io/badge/version-11.0--Omni--Perception-blueviolet?style=for-the-badge)](https://github.com/voodooq/wechatAGENT)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)

**IronSentinel** 是一个开源、自治、高度透明的 AI 智能助理演化体。它不仅仅是一个简单的聊天机器人，而是一个具备**全感知能力**（Omni-Perception）、**自省机制**（Self-introspection）和**环境自愈能力**（Self-healing）的数字生命体雏形。

---

## 🌟 核心理念 (Vision)

- **完全自省**: AI 实时感知自身拥有的工具集，动态生成身份边界，拒绝认知冲突。
- **环境自愈**: 具备自动补全二进制环境、自动提权以及全链路编码校准的能力。
- **物理寻踪**: 在 Windows 环境下实现精准的路径探测。
- **透明演化**: 透明地汇报代码修改逻辑，支持热重载，实现“自我编写，自我运行”。

---

## 🚀 核心功能 (Features)

### 🧠 1. 自省大脑 (Omni-Brain)
- **动态 Prompt**: 调用 `AgentBrain` 根据 `ToolManager` 实时扫描出的 20+ 工具动态生成 Meta-Prompt。
- **认知对齐**: 彻底消除“AI 否定自身能力”的逻辑断层，只要工具箱里有，它就能做到。

### 🎙️ 2. 全路径语音感知 (Shadow Decoder)
- **超级定位雷达**: 通过 `ultra_wechat_locator` 精准锁定微信语音物理存放目录，适配多用户及注册表占位符。
- **头部自修复**: 自动修复微信加密 Silk 原始流的头信息，确保 100% 解码成功。
- **多媒体回复**: 支持从 ASR 转录到 TTS 语音下发的全闭环。

### 🛠️ 3. 系统级演化能力 (Self-Evolution)
- **代码重写**: 使用 `evolve_code` 实时修改系统逻辑。
- **二进制守备**: 自动下载并校验 ffmpeg、silk_v3 等核心组件。
- **Winget 集成**: 支持通过微软 Winget 包管理器静默安装 Windows 软件。

### 🛡️ 4. 稳健内核 (Iron Kernel)
- **权限守卫**: 自动驱动管理员模式以访问受限资源。
- **编码对齐**: 全链路强制 `chcp 65001` (UTF-8)，彻底杜绝 Windows 下的乱码崩溃。
- **会话隔离**: 基于微信备注名的多维度上下文记忆管理。

---

## 📂 项目结构 (Structure)

```text
wechatAGENT/
├── core/                   # 核心大脑与逻辑
│   ├── brain.py            # 自省中枢
│   ├── tool_manager.py     # 动态工具管理器
│   ├── agent.py            # LangChain Agent 集成
│   └── tools/              # 核心演化与解码工具
├── kernel/                 # 内核级守门员
│   ├── bin/                # 存放 SILK/FFMPEG 二进制文件
│   └── privilege_guard.py  # 管理员提权逻辑
├── tools/                  # 业务工具库 (RPA, Search, Data...)
├── wechat/                 # 微信 UI 自动化监听与发送
├── worker/                 # 异步任务处理器
├── utils/                  # 稳定性、日志与自检工具
└── main.py                 # 程序启动入口
```

---

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆仓库
git clone https://github.com/your-username/wechatAGENT.git
cd wechatAGENT

# 创建虚拟环境（推荐使用conda）
conda create -n wechat-ai python=3.10
conda activate wechat-ai

# 安装依赖
pip install -r requirements-lock.txt
```

### 2. 配置环境变量
```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入您的 API Keys
# 支持 Google、OpenAI、Anthropic、DeepSeek、Qwen 等多种 AI 模型
```

### 3. 初始化二进制组件
```bash
# 运行初始化脚本（确保silk_v3_decoder.exe等组件可用）
python tools/initialize_env.py
```

> **注意**: [silk_v3_decoder.exe](file://e:\work\wechatAGENT\tools\bin\silk_v3_decoder.exe) 是微信语音解码的核心组件，已包含在仓库中。如果文件缺失，请确保从 Git 仓库完整克隆，或手动下载放置到 `tools/bin/` 目录。

### 4. 启动主程序
```bash
python main.py
```

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

### 方法三：守护模式运行
```bash
# 使用守护进程模式，增强稳定性
run_sentinel.bat
```

---

## 🧬 演化协议 (Evolution Protocol)

IronSentinel 遵循**透明演化闭环**:
1. **汇报**: 接收指令后，通过 `report_evolution_progress` 同步计划。
2. **编码**: 自主生成演化补丁。
3. **重启**: 请求 `request_hot_reload`，系统重生后自动向主人发送成功喜报。

---

## ⚙️ 详细配置指南

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

---

## 🛠️ 开发与扩展

### 项目结构详解
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

### 代码演化流程
IronSentinel 支持透明演化闭环：
1. **汇报**: 接收指令后，通过 `report_evolution_progress` 同步计划
2. **编码**: 使用 `evolve_code` 工具进行代码修改
3. **重启**: 请求 `request_hot_reload`，系统重生后自动发送成功通知

### 调试与日志
- 日志文件保存在 `logs/` 目录
- 支持不同日志级别：DEBUG, INFO, WARNING, ERROR
- 可以通过 `.env` 中的 `LOG_LEVEL` 配置日志级别

---

## 📖 详细开发文档

完整的开发指南请查看 [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)，包含：
- 详细的项目架构说明
- 核心模块功能详解
- 环境要求与配置
- 常见问题解决方案
- 安全注意事项
- 贡献指南

---

## 🔧 运行模式

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

---

## ❓ 常见问题

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

---

## ⚠️ 隐私与安全
- **隔离区**: 严禁 AI 触碰 `core/config_private.py`。
- **二次确认**: 敏感系统指令（如关机、删库）必须通过微信回复 `!confirm <Token>` 确认。

---

## 👨💻 贡献者
- **Master**: 虎哥
- **Design & Coding**: 铁卫 (Self-Evolution Component)

---
> "I am IronSentinel. I perceive, I code, I evolve."
