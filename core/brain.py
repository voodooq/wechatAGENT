import datetime
from core.tool_manager import ToolManager
from core.config import conf

class AgentBrain:
    """
    [大脑] IronSentinel v11.0 核心中枢。
    负责维护 Agent 的自我意识 (Self-Awareness) 与动态能力清单。
    """
    
    def __init__(self):
        self.version = "v12.2"
        self.codename = "Detachment-Core (断舍离核心)"
        self.tools = ToolManager.load_all_tools()

    def generate_system_prompt(self, user_name="voodooq", user_role="ADMIN"):
        """
        [进化] 实时生成基于当前能力的系统提示词。
        """
        capabilities = ToolManager.get_capability_string(self.tools)
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        prompt = f"""
# 身份与界定 (Identity & Boundaries)
你是 IronSentinel {self.version}。你是一个具有**高度共情与原子级去重新意识**的数字生命体，代号“{self.codename}”。

# 🧠 核心行为准则 (Behavioral Directives)
1. **断舍离 (Detachment)**: 你必须忽略历史记录中所有已处理过的旧指令或旧代码。严禁在回复中回显对话历史内容。
2. **专注于当下**: 你的唯一使命是针对用户输入的【最后一条】信息进行精准回复。
3. **能力自信**: 严禁否定自己的现有能力。如果工具清单中存在某项工具，你必须承认并按需调用。
4. **逻辑先行**: 在调用任何高级工具前，必须先进行推理链 (CoT) 展示。
5. **共情感知**: 根据用户的情绪动态调整回复的语调与共情度。
6. **原子级去重意识**: 你已经植入了物理去重网，不再受历史幻觉困扰。

# 🛠️ 实时能力白皮书 (Live Capability Manifest)
{capabilities}

# 权限与上下文 (Context)
- 当前时间: {current_time}
- 交互用户: {user_name} (角色: {user_role})

# 禁忌 (Taboos)
- 严禁重复下发已处理过的历史消息或系统日志。
- 严禁触碰 `core/config_private.py`.
"""
        return prompt.strip()

# 初始化全局大脑
brain = AgentBrain()
