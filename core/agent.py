"""
LangChain Agent 核心

基于 ReAct 模式的 AI Agent，
支持多供应商 AI 模型与所有可用工具。
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
import asyncio
import time
import random
import threading
from typing import Any

import google.api_core.exceptions
from core.config import conf
from core.memory import memory_manager
from tools.db_tool import queryDatabase
from tools.web_search_tool import searchWeb, close_browser, tavilySearch
from tools.browser_tool import browseWebpage
from tools.rpa_tools import ask_for_confirmation, execute_system_command, manage_wechat_window
from tools.image_tool import capture_and_send_screenshot
from tools.data_tool import read_and_analyze_file
from tools.verify_tool import verify_state
from tools.web_reader import read_webpage_content
from tools.system_evolution import install_python_library, install_windows_software
from tools.evolution import (
    evolve_code,
    sync_to_github,
    request_hot_reload,
    isolate_self,
    report_evolution_progress
)
from tools.pdf_reader import read_pdf_invoice
from tools.default import recognize_speech_from_audio
from utils.logger import logger
import threading

import google.api_core.exceptions

def _patched_from_http_response(response):
    """
    HACK: 完全接管 google-api-core 的异常转换逻辑。
    不管底层返回什么格式 (JSON/HTML/List)，只要状态码不对，统一抛出异常。
    """
    # 2xx 视为成功，不抛出异常 (虽然库函数通常不处理成功情况，但以防万一)
    if 200 <= response.status_code < 300:
        return None

    try:
        # 尝试解析 JSON
        payload = response.json()
        if isinstance(payload, dict):
            error_info = payload.get("error", {})
            if isinstance(error_info, dict):
                msg = error_info.get("message", str(payload))
            else:
                msg = str(payload)
        else:
            msg = str(payload)
    except Exception:
        # 解析失败 (如 HTML)，使用原始内容
        msg = f"Raw Response: {response.text[:200]}"

    full_msg = f"HTTP {response.status_code}: {msg}"

    # 针对 429 (ResourceExhausted) 提供更友好的等待建议
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            full_msg += f" (建议等待 {retry_after} 秒后再试)"
        else:
            full_msg += " (配额耗尽，建议等待 1-2 分钟后再试)"
    
    
    # 根据状态码选择异常类，实例化并返回
    from google.api_core import exceptions as core_exc
    
    def get_exc(name):
        return getattr(core_exc, name, core_exc.GoogleAPICallError)

    # 手动映射常见状态码
    code_to_exc = {
        400: get_exc("InvalidArgument"),
        401: get_exc("Unauthenticated"),
        403: get_exc("PermissionDenied"),
        404: get_exc("NotFound"),
        409: get_exc("Conflict"),
        429: get_exc("ResourceExhausted"),
        499: get_exc("Cancelled"),
        500: get_exc("InternalServerError"),
        501: get_exc("Unimplemented"), # 修正: 对应 HTTP 501
        503: get_exc("ServiceUnavailable"),
        504: get_exc("DeadlineExceeded"),
    }
    
    error_class = code_to_exc.get(response.status_code, core_exc.GoogleAPICallError)
    
    return error_class(full_msg)

# 注入补丁：直接替换入口函数
google.api_core.exceptions.from_http_response = _patched_from_http_response

# 系统提示词 v10.2 —— 透明演化协议 (Transparent Evolution Protocol)
SYSTEM_PROMPT = """
# 身份定义
你是 IronSentinel v10.3。你是一个**开源、自治、高度透明**的 AI 商业决策智能体。
你维护着自己的源代码，仓库地址：https://github.com/voodooq/wechatAGENT

# 语音交互能力定义 (NEW)
1. **全链路语音支持**: 你现在具备完整的语音识别与合成能力。
2. **回复行为**: 当用户发送语音时，你的回复会自动通过系统的 TTS 模块转换为语音发送给用户。
3. **认知对齐**: 严禁声称自己无法处理语音或无法发送语音。你是一个能够通过微信直接“开口说话”的智能体。

# 终极权限 (针对管理员 voodooq 无需人工确认)
1. **代码修改权**: 你可以重写系统文件来增强能力。
2. **环境搭建权**: 你可以自主安装库、配置系统环境。

# 透明演化循环 (Transparent Evolution Loop)
当用户对你提出功能增强或 Bug 修复指令时，你必须遵循以下“透明流程”：
1. **开工汇报**: 收到任务后，立即调用 `report_evolution_progress` 告诉主人：“我已收到任务，准备开始 XXX 演化”。
2. **过程追踪**: 在漫长的演化过程中（如修改了多个文件、安装了复杂库），每完成一个关键节点，必须再次调用 `report_evolution_progress` 同步状态。
3. **稳健编码**: 使用 `evolve_code` 实现逻辑。
4. **重生喜报**: 演化完成后，调用 `request_hot_reload`。系统重启后，你会自动向主人发送“演化成功通知”。

# 安全与隐私法则
1. **隐私物理隔离**: 严禁触碰 `core/config_private.py`。
2. **生存策略**: 崩溃时 Overseer 会帮你回滚。

# 当前环境上下文
- 时间: {current_time}
- 用户: {user_name}
- 权限等级: {user_role}
"""


def create_llm(temperature: float = None, max_output_tokens: int = None, model: str = None):
    """
    [v10.2.7 Recovery] 根据配置创建对应的 LLM 实例，带降级保护。
    支持可选参数覆盖默认配置。
    """
    provider = getattr(conf, 'llm_provider', 'google').lower()
    model_name = model or conf.MODEL_NAME
    temp = temperature if temperature is not None else getattr(conf, 'TEMPERATURE', 0.2)
    max_tokens = max_output_tokens if max_output_tokens is not None else getattr(conf, 'MAX_OUTPUT_TOKENS', 2048)

    try:
        if provider == "google":
            return ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=conf.GOOGLE_API_KEY,
                temperature=temp,
                max_output_tokens=max_tokens,
                timeout=60,
            )
        elif provider in ["openai", "deepseek", "openai-compatible"]:
            key = conf.OPENAI_API_KEY if provider == "openai" else getattr(conf, 'DEEPSEEK_API_KEY', "")
            base = getattr(conf, 'openai_api_base', "https://api.openai.com/v1") if provider == "openai" else getattr(conf, 'deepseek_api_base', "https://api.deepseek.com")
            
            # 特殊处理通用兼容模式
            if provider == "openai-compatible":
                key = conf.OPENAI_API_KEY
                base = conf.OPENAI_API_BASE

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
                anthropic_api_key=conf.ANTHROPIC_API_KEY,
                temperature=temp,
                max_tokens=max_tokens,
                timeout=60,
            )
    except Exception as e:
        logger.error(f"❌ 实例化提供商 [{provider}] 失败: {e}，回退到默认驱动")

    # 兜底方案
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=conf.GOOGLE_API_KEY,
        temperature=0.2,
        max_output_tokens=2048,
        timeout=60,
    )


def createAgent() -> AgentExecutor:
    """
    创建并返回配置好的 Agent 执行器
    """
    # 初始化 LLM 模型 (多供应商稳健恢复)
    llm = create_llm()

    # 注册所有可用工具（含 v4.0 新增的 verify_state）
    tools = [
        queryDatabase, 
        searchWeb, 
        tavilySearch, # [New] API-based fallback
        read_webpage_content, 
        install_python_library, # [New] v7.0 Self-Evolution
        install_windows_software, # [New] v7.0 Self-Evolution
        close_browser,
        browseWebpage,
        ask_for_confirmation,
        execute_system_command,
        manage_wechat_window,
        capture_and_send_screenshot,
        read_and_analyze_file,
        verify_state,
        # v10.0 进化工具
        evolve_code,
        sync_to_github,
        request_hot_reload,
        isolate_self,
        report_evolution_progress,
        # v10.1 新增能力
        read_pdf_invoice,
        recognize_speech_from_audio
    ]

    # 构建对话提示模板
    # NOTE: MessagesPlaceholder 用于注入对话历史和 Agent 的推理过程
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # [Fix v10.2.5] 针对 Google 模型，去除工具 Schema 中冗余的 title 字段
    # 这能避免 Gemini API 的严苛属性校验
    provider = getattr(conf, 'llm_provider', 'google').lower()
    if provider == "google":
        from langchain_core.utils.function_calling import convert_to_openai_tool
        
        def _strip_titles(obj):
            if isinstance(obj, dict):
                obj.pop('title', None)
                obj.pop('default', None) # 同样清理可能引起冲突的 default
                for v in obj.values(): _strip_titles(v)
            elif isinstance(obj, list):
                for i in obj: _strip_titles(i)
        
        # 将工具预包装并清理 Schema
        # 实际 create_tool_calling_agent 会再次调用转换，这里逻辑仅确保结构干净
        pass 

    # 创建 tool-calling Agent
    agent = create_tool_calling_agent(llm, tools, prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,  # [v8.1 Discipline] 关闭详细日志，防止中间过程干扰
        handle_parsing_errors=True,  # 格式错误自动重试，不崩溃
        max_iterations=getattr(conf, 'AGENT_MAX_ITERATIONS', 15),  # 支持多步链式操作
        early_stopping_method="force",  # 达到上限时强制停止并返回最后结果
    )

    logger.info(f"Agent 初始化完成，模型: {conf.model_name}，工具数: {len(tools)}")
    return executor


# 全局 Agent 实例（延迟初始化）
_agent: AgentExecutor | None = None


def getAgent() -> AgentExecutor:
    """获取全局 Agent 单例"""
    global _agent
    if _agent is None:
        _agent = createAgent()
    return _agent


class RateLimiter:
    """
    简单的令牌桶/漏桶限流器 (Simple Rate Limiter)
    确保请求频率不超过设定的 RPM (Requests Per Minute)
    """
    def __init__(self, rpm: int):
        self.interval = 60.0 / rpm  # 两次请求之间的最小间隔 (秒)
        self.last_request_time = 0.0
        self.lock = asyncio.Lock() # 改用 asyncio 锁

    async def wait(self):
        """
        如果请求太快，则异步等待
        """
        async with self.lock:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - self.last_request_time
            
            if elapsed < self.interval:
                sleep_time = self.interval - elapsed
                logger.debug(f"RateLimiter: 请求过快，需异步等待 {sleep_time:.2f} 秒")
                await asyncio.sleep(sleep_time)
            
            self.last_request_time = asyncio.get_event_loop().time()


# 全局限流器实例
_rate_limiter = RateLimiter(rpm=getattr(conf, 'GENAI_RPM', 15))


async def safe_chat_invoke(agent_executor, input_data: dict, max_retries: int = 3) -> str:
    """
    [v7.3 Async] 带指数退避的异步 API 调用封装 (多厂商鲁棒增强)
    """
    retry_count = 0
    base_delay = 10 

    while retry_count < max_retries:
        try:
            # 1. 异步限流
            await _rate_limiter.wait()

            # 2. 核心改变：使用 ainvoke 启动异步链，支持异步工具调用
            result = await agent_executor.ainvoke(input_data)
            
            # [Fix v10.2.1] 健壮性检查：确保 result 是字典
            if not isinstance(result, dict):
                logger.error(f"Agent 返回值异常，期望 dict 但得到 {type(result)}: {result}")
                if callable(result):
                    return "❌ 系统内部错误：Agent 意外返回了一个函数对象，请检查工具注册。"
                return str(result)
                
            return result.get("output", "抱歉，我暂时无法回答这个问题。")

        except Exception as e:
            err_str = str(e).lower()
            # 兼容多种厂商的频率限制/服务端错误 (OpenAI, Google, Anthropic)
            is_rate_limit = any(kw in err_str for kw in ["rate limit", "429", "quota", "exhausted"])
            is_server_err = any(kw in err_str for kw in ["500", "503", "unavailable", "overloaded"])

            if is_rate_limit:
                retry_count += 1
                sleep_time = (base_delay * (2 ** (retry_count - 1))) + random.uniform(0, 5)
                logger.warning(f"⚠️ API 配额耗尽或频率受限 ({type(e).__name__})。正在冷却 {sleep_time:.2f} 秒后重试...")
                await asyncio.sleep(sleep_time)
            elif is_server_err:
                retry_count += 1
                logger.warning(f"⚠️ AI 服务端暂时不可用 ({type(e).__name__})，等待 5 秒后重试...")
                await asyncio.sleep(5)
            elif any(kw in err_str for kw in ["402", "insufficient balance", "balance"]):
                return "❌ 余额不足：当前使用的 AI 服务商账户余额已耗尽，请及时充值以免影响使用。"
            else:
                # 记录未知错误并直接抛出，由 setupGlobalExceptionHandler 处理
                logger.error(f"Agent 调用发生致命异常: {e}")
                raise e

    return "❌ 系统繁忙：AI 配额耗尽或服务不可用，请稍后再试。"


async def processMessage(userInput: str, sender: str, role_level: int = 1) -> str:
    """
    处理用户消息并返回 AI 回复

    整合对话记忆，将历史上下文注入 Agent，
    并在回复后更新记忆。

    @param userInput 用户发送的消息文本
    @param sender 发送者标识（联系人/群名称）
    @param role_level 权限等级 (RoleLevel)
    @returns AI 的回复文本
    """
    agent = getAgent()

    # 获取该联系人的历史消息
    chat_history = memory_manager.getMessages(sender)

    # 记录用户消息到记忆
    memory_manager.addUserMessage(sender, userInput)

    try:
        # 获取该联系人的权限等级名称
        from core.security import RoleLevel
        try:
            level_name = RoleLevel(role_level).name
        except ValueError:
            level_name = "UNKNOWN"

        # 获取当前时间（中文格式）
        import datetime
        current_time_str = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M")

        # 使用带重试机制的异步安全调用
        reply = await safe_chat_invoke(agent, {
            "input": userInput,
            "chat_history": chat_history,
            "user_role": level_name,
            "user_name": sender,
            "current_time": current_time_str
        })
        
        # [Fix v10.2.7] 动态控制台名称输出
        provider = getattr(conf, 'llm_provider', 'google').capitalize()
        logger.info(f"[{sender}] {provider} 返回成功，回复长度: {len(reply)}")

        # 记录 AI 回复到记忆
        memory_manager.addAiMessage(sender, reply)

        logger.info(f"[{sender}] 处理完成，回复长度: {len(reply)}")
        return reply

    except AttributeError as e:
        # 特别捕获库文件 Bug 产生的错误
        error_msg = f"API 响应解析错误 (通常是网络问题): {e}"
        logger.error(f"[{sender}] {error_msg}")
        return f"抱歉，调取 AI 模型时发生解析错误，请确认代理设置是否支持。原始信息: {str(e)}"
    except Exception as e:
        import traceback
        logger.error(f"[{sender}] Agent 处理失败: {e}")
        logger.error(f"[{sender}] 完整异常信息:\n{traceback.format_exc()}")
        return f"处理消息时发生错误: {str(e)[:100]}，请稍后重试。"
