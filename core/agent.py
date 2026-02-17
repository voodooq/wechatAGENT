"""
LangChain Agent 核心

基于 ReAct 模式的 AI Agent，
支持多供应商 AI 模型与所有可用工具。
"""
import asyncio
import os
from typing import Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from core.tool_manager import ToolManager
from core.config import conf
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
        model_name = getattr(conf, 'llm_model', 'gemini-1.5-flash')
        temp = getattr(conf, 'temperature', 0.7)
        max_tokens = getattr(conf, 'max_tokens', 4096)
        
        # 创建聊天模型
        chat_model = get_chat_model(provider, model_name, conf, temp, max_tokens)
        
        # 获取可用工具
        tool_manager = ToolManager()
        tools = tool_manager.get_all_tools()
        
        # 构建系统提示
        system_prompt = _build_system_prompt(sender, role_level)
        
        # 创建 ReAct Agent
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
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

你可以使用以下工具来帮助用户：
- 微信相关操作（发送消息、处理语音等）
- 网络搜索和信息获取
- 文件处理和数据操作
- 系统管理和环境配置
- 语音识别和文本转语音

请根据用户的需求选择合适的工具，并提供清晰、准确的回答。"""
    
    return base_prompt.format(sender=sender, role_level=role_level)