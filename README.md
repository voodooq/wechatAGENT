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

## 🏗️ 快速启动 (Quick Start)

### 1. 环境依赖
确保安装了 [Conda](https://www.anaconda.com/) 或 Python 3.10+。

```bash
conda create -n wechat-ai python=3.10
conda activate wechat-ai
pip install -r requirements.txt
```

### 2. 配置 .env
将 `.env.example` 复制为 `.env` 并填入你的 API Key (Google, OpenAI, etc.)。

### 3. 初始化二进制环境
```bash
python tools/initialize_env.py
```

### 4. 运行
```bash
python main.py
```

---

## 🧬 演化协议 (Evolution Protocol)

IronSentinel 遵循**透明演化闭环**:
1. **汇报**: 接收指令后，通过 `report_evolution_progress` 同步计划。
2. **编码**: 自主生成演化补丁。
3. **重启**: 请求 `request_hot_reload`，系统重生后自动向主人发送成功喜报。

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
