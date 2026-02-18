"""
LangChain Agent 核心

基于 ReAct 模式的 AI Agent，
支持多供应商 AI 模型与所有可用工具。
新增: OpenClaw 代理对接支持
"""
import asyncio
import os
from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from core.tool_manager import ToolManager
from core.config import conf
from core.openclaw_bridge import OpenClawChatModel
from utils.logger import logger



def get_chat_model(provider, model_name, conf, temp=0.7, max_tokens=4096):
    if provider == "google":
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=conf.google_api_key,
            temperature=temp,
            max_output_tokens=max_tokens,
            timeout=60,
        )
    elif provider in ["openai", "deepseek", "openai-compatible"]:
        key = conf.openai_api_key if provider == "openai" else getattr(conf, 'deepseek_api_key', "")
        base = getattr(conf, 'openai_api_base', "https://api.openai.com/v1") if provider == "openai" else getattr(conf, 'deepseek_api_base', "https://api.deepseek.com")
        
        # 特殊处理通用兼容模式
        if provider == "openai-compatible":
            key = conf.openai_api_key
            base = conf.openai_api_base

        return ChatOpenAI(
            model=model_name,
            openai_api_key=key,
            openai_api_base=base,
            temperature=temp,
            max_tokens=max_tokens,
            timeout=60,
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model=model_name,
            anthropic_api_key=conf.anthropic_api_key,
            temperature=temp,
            max_tokens=max_tokens,
            timeout=60,
        )
    elif provider == "openclaw":
        # OpenClaw 代理对接
        return OpenClawChatModel(
            api_base=getattr(conf, 'openclaw_api_base', "http://localhost:9847"),
            session_key=getattr(conf, 'openclaw_session_key', ""),
            temperature=temp,
            max_tokens=max_tokens,
        )
    # Qwen support temporarily disabled due to missing dependency
    # elif provider == "qwen":
    #     return ChatQwen(
    #         model=model_name,
    #         qwen_api_key=conf.qwen_api_key,
    #         temperature=temp,
    #         max_tokens=max_tokens,
    #         timeout=60,
    #     )


async def processMessage(userInput: str, sender: str, role_level: int = 1) -> Optional[str]:
    """
    处理用户消息并返回 AI 回复
    
    Args:
        userInput: 用户输入内容
        sender: 发送者标识
        role_level: 用户角色级别（1-普通用户，2-管理员等）
        
    Returns:
        AI 生成的回复文本，如果处理失败则返回 None
    """
    try:
        # 获取配置
        provider = getattr(conf, 'llm_provider', 'google')
        # 修复：使用 model_name 而不是 llm_model
        model_name = getattr(conf, 'model_name', 'gemini-1.5-flash')
        temp = getattr(conf, 'temperature', 0.7)
        max_tokens = getattr(conf, 'max_tokens', 4096)
        
        # 创建聊天模型
        chat_model = get_chat_model(provider, model_name, conf, temp, max_tokens)
        
        # 获取可用工具
        tool_manager = ToolManager()
        tools = tool_manager.load_all_tools()
        
        # 构建系统提示
        system_prompt = _build_system_prompt(sender, role_level)
        
        # 创建 ReAct Agent
        # ReAct 提示词模板
        react_instruction = """
TOOLS:
------
You have access to the following tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```
"""
        full_system_prompt = system_prompt + "\n\n" + react_instruction



        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(full_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}\n\n{agent_scratchpad}"),
        ])
        
        agent = create_react_agent(chat_model, tools, prompt)

        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            return_intermediate_steps=False
        )
        
        # 执行 Agent
        result = await agent_executor.ainvoke({
            "input": userInput,
            "chat_history": []
        })
        
        reply = result.get("output", "").strip()
        logger.info(f"Agent 生成回复: {reply[:100]}...")
        return reply
        
    except Exception as e:
        logger.error(f"Agent 处理消息失败: {e}")
        return None


def _build_system_prompt(sender: str, role_level: int) -> str:
    """
    构建系统提示词
    """
    base_prompt = """你是一个智能助理，名为 IronSentinel。你的任务是帮助用户解决问题，提供有用的信息，并执行各种工具操作。
    
当前用户: {sender}
用户权限级别: {role_level}

## 重要搜索规则

### 网站限定处理
- 当用户明确指定在某个网站搜索时（如"在xxx网站上查找"、"从xxx平台获取"等），你必须只在该指定网站内进行搜索
- 构造搜索查询时，使用 "site:域名 关键词" 的格式来限定搜索范围
- 例如：用户说"在中国击剑协会官网查找比赛信息"，你应该构造查询 "site:fencing.sport.org.cn 比赛信息"

### 时间参数处理  
- 年份未指定时，默认使用当前年份（2026年）
- 月份未指定时，默认使用当前月份（2月）
- 日期未指定时，默认使用当天日期（17日）
- 在构造搜索查询时，自动补充完整的时间信息
- 例如：用户说"查找3月份的比赛"，你应该理解为"2026年3月的比赛"

### 工具使用规范
你可以使用以下工具来帮助用户：
- 微信相关操作（发送消息、处理语音等）
- 网络搜索和信息获取
- 文件处理和数据操作
- 系统管理和环境配置
- 语音识别和文本转语音

### 回复要求
- 提供清晰、准确、有用的回答
- 如果搜索结果不相关或不足，请明确告知用户
- 避免猜测或编造信息

请严格遵守以上规则，确保搜索结果的准确性和相关性。"""
    
    return base_prompt.format(sender=sender, role_level=role_level)


def create_llm(temperature: float = 0.7, max_tokens: int = 4096):
    """
    创建 LLM 实例用于日常摘要生成
    
    Args:
        temperature: 温度参数
        max_tokens: 最大输出令牌数
        
    Returns:
        配置好的 LLM 实例
    """
    from core.config import conf
    
    provider = getattr(conf, 'llm_provider', 'google')
    # 修复：使用 model_name 而不是 llm_model
    model_name = getattr(conf, 'model_name', 'gemini-1.5-flash')
    
    return get_chat_model(provider, model_name, conf, temperature, max_tokens)
