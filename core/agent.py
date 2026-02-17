"""
LangChain Agent 核心

基于 ReAct 模式的 AI Agent，
支持多供应商 AI 模型与所有可用工具。
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatQwen
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


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
    elif provider == "qwen":
        return ChatQwen(
            model=model_name,
            qwen_api_key=conf.qwen_api_key,
            temperature=temp,
            max_tokens=max_tokens,
            timeout=60,
        )
