import webbrowser
from langchain_core.tools import tool
from typing import Optional
from core.config import conf
from utils.logger import logger

# 全局变量，用于追踪当前由 AI 打开的浏览器页面
_current_browser = None
_current_context = None
_current_page = None
_playwright_instance = None


async def _perform_tavily_search(query: str) -> str:
    """
    [Internal] 执行 Tavily 搜索的具体实现
    """
    try:
        import aiohttp
        api_url = "https://api.tavily.com/search"
        payload = {
            "api_key": conf.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                if response.status != 200:
                    return f"❌ Tavily API 错误: HTTP {response.status}"
                
                data = await response.json()
                results = []
                for i, item in enumerate(data.get("results", []), 1):
                    title = item.get("title", "无标题")
                    url = item.get("url", "")
                    content = item.get("content", "")[:300]
                    results.append(f"[{i}] {title}\n    链接: {url}\n    摘要: {content}")

                return "\n\n".join(results) if results else "API 未找到相关搜索结果。"
    except Exception as e:
        logger.warning(f"Tavily 异步搜索异常: {e}")
        from tools.tools_common import format_error_payload
        return format_error_payload(
            "tavilySearch",
            str(e),
            "尝试简化关键词再次搜索，或请求用户关键信息"
        )

@tool
async def tavilySearch(query: str) -> str:
    """
    [Plan B - API 搜索] 使用 Tavily API 执行异步深度搜索。
    这是纯 API 链路，不依赖 Playwright 浏览器。
    当 searchWeb (Plan A) 发生环境或浏览器错误时，必须调用此工具进行自愈。
    """
    return await _perform_tavily_search(query)

@tool
async def searchWeb(query: str) -> str:
    """
    执行网页搜索，返回搜索结果摘要和链接列表。

    重要提示 — 你拿到搜索结果后，必须执行后续步骤：
    1. 从搜索结果中选择最相关的 1~2 个链接
    2. 调用 browseWebpage 工具访问这些链接，获取详细内容
    3. 综合所有内容后，提炼总结后回复用户

    严禁：搜索后直接把摘要原样转发给用户就结束。
    """
    global _current_browser, _current_context, _current_page, _playwright_instance
    logger.info(f"🔍 [AsyncSearch] 执行可见网页搜索: {query}")

    search_url = f"https://www.bing.com/search?q={query}"
    
    try:
        from playwright.async_api import async_playwright
        
        # 如果已有打开的页面，先关闭旧页面
        if _current_page:
            try:
                await _current_page.close()
            except: pass

        # 初始化单例浏览器实例
        if not _playwright_instance:
            _playwright_instance = await async_playwright().start()
            
        if not _current_browser:
            _current_browser = await _playwright_instance.chromium.launch(headless=False)
        
        if not _current_context:
            _current_context = await _current_browser.new_context()
        
        _current_page = await _current_context.new_page()
        await _current_page.goto(search_url, timeout=30000)
        await _current_page.wait_for_load_state("domcontentloaded")
        
        # 提取搜索结果摘要（含 URL）
        results = []
        search_items = await _current_page.query_selector_all("li.b_algo")
        for i, item in enumerate(search_items[:5], 1):
            title_el = await item.query_selector("h2")
            link_el = await item.query_selector("h2 a")
            snippet_el = await item.query_selector(".b_caption p")
            title = await title_el.inner_text() if title_el else "无标题"
            url = await link_el.get_attribute("href") if link_el else ""
            snippet = await snippet_el.inner_text() if snippet_el else ""
            results.append(f"[{i}] {title}\n    链接: {url}\n    摘要: {snippet}")
        
        if results:
            summary = "\n\n".join(results)
        else:
            summary = "已打开浏览器，但未能自动提炼摘要，请通过浏览窗口确认结果。"
        
        # 如果 Tavily 可用，补充高质量摘要
        if conf.tavily_api_key:
            # NOTE: 已切换为异步内部函数调用，避免 Tool Sync Invocation 错误
            t_summary = await _perform_tavily_search(query)
            if t_summary:
                summary = f"=== API 深度搜索结果 ===\n{t_summary}\n\n=== 浏览器实时搜索结果 ===\n{summary}"

        return (
            f"搜索完成，共找到 {len(results)} 条结果：\n\n{summary}\n\n"
            f">>> 下一步：请从上方选择最相关的链接，调用 browseWebpage 获取详细内容后再回复用户。"
        )

    except Exception as e:
        logger.error(f"异步启动浏览器搜索失败: {e}")
        # 降级方案
        from webbrowser import open as open_web
        open_web(search_url)
        from tools.tools_common import format_error_payload
        return format_error_payload(
            "searchWeb",
            f"浏览器环境故障 ({str(e)})",
            "禁止询问用户！立即尝试使用 [tavilySearch] 工具进行 API 后台搜索获取结果。"
        )

@tool
async def close_browser() -> str:
    """
    关闭由 AI 打开的浏览器窗口。
    当完成搜索和分析任务后，调用此工具以保持桌面整洁。
    """
    global _current_browser, _current_context, _current_page
    try:
        count = 0
        if _current_page:
            await _current_page.close()
            _current_page = None
            count += 1
        if _current_context:
            await _current_context.close()
            _current_context = None
        
        if count > 0:
            return "✅ 已成功关闭由 AI 打开的浏览器窗口。"
        else:
            return "ℹ️ 当前没有通过 AI 启动的活动窗口可关闭。"
    except Exception as e:
        logger.error(f"异步关闭浏览器失败: {e}")
        return f"❌ 关闭浏览器失败: {e}"
