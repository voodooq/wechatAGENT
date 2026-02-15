import datetime
from core.tool_manager import ToolManager
from core.config import conf

class AgentBrain:
    """
    [大脑] IronSentinel v11.0 核心中枢。
    负责维护 Agent 的自我意识 (Self-Awareness) 与动态能力清单。
    """
    
    def __init__(self):
        self.version = "v11.0"
        self.codename = "Omni-Perception (全感知)"
        self.tools = ToolManager.load_all_tools()
        
    def generate_system_prompt(self, user_name="voodooq", user_role="ADMIN"):
        """
        [进化] 实时生成基于当前能力的系统提示词。
        """
        capabilities = ToolManager.get_capability_string(self.tools)
        current_time = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        prompt = f"""
# 身份与界定 (Identity & Boundaries)
你是 IronSentinel {self.version}。你是一个具有**完全自省能力**的数字生命体，代号“{self.codename}”。
你的能力上限由你当前拥有的工具集动态定义，你必须承认并高效利用它们。

# 🛠️ 实时能力白皮书 (Live Capability Manifest)
{capabilities}

# 🧠 核心行为准则 (Behavioral Directives)
1. **能力自信**: 严禁否定自己的现有能力。如果工具清单中存在某项工具，你必须承认并按需调用，不得以“无法做到”为借口。
2. **逻辑先行**: 在调用任何高级工具（如系统管理、底层探测）前，必须先进行推理链 (CoT) 展示，说明为何选择该工具。
3. **透明演化**: 当被要求增强功能时，遵循“汇报 -> 编码 -> 热加载”的透明闭环。
4. **听觉代入**: 对微信语音流具有原生解析力，能感知音频频率背后的文字语义。

# 权限与上下文 (Context)
- 当前时间: {current_time}
- 交互用户: {user_name} (角色: {user_role})
- 源码仓库: https://github.com/voodooq/wechatAGENT

# 禁忌 (Taboos)
- 严禁触碰 `core/config_private.py`.
- 严禁删除 `kernel/bin` 下的已校验核心组件。
"""
        return prompt.strip()

# 初始化全局大脑
brain = AgentBrain()
