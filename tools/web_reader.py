import html2text
from langchain_core.tools import tool
from playwright.sync_api import sync_playwright
from utils.logger import logger

# [NEW] IronSentinel v5.0 核心能力：网页文本深度阅读器
# 将复杂的 HTML 转换为 AI 易读的 Markdown，并进行长度截断保护

def _html_to_markdown(html_content: str) -> str:
    """内部辅助：将 HTML 转换为 Markdown 文本"""
    h = html2text.HTML2Text()
    h.ignore_links = True  # 保护 Token，忽略超链接
    h.ignore_images = True # 保护 Token，忽略图片
    h.body_width = 0       # 不限制行宽
    return h.handle(html_content)

@tool
async def read_webpage_content(url: str) -> str:
    """
    [核心工具] 深度阅读网页的正文内容。
    当你通过 searchWeb 获得了一组链接，但摘要信息不足以回答用户问题时，
    你应该挑选出最相关的 1~2 个链接，调用此工具“点进去”看详细内容。
    
    参数:
    - url: 必须是完整的 http/https 链接。
    """
    logger.info(f"⏳ [AsyncReader] 正在深度阅读网页: {url}")
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # 🚨 强制修复并清洗 URL
            url = url.strip()
            if not url.startswith('http'):
                url = 'https://' + url

            # 使用更长的超时并等待 DOM 加载
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # 获取内容
            html_content = await page.content()
            await browser.close()
            
            # 转换为 Markdown
            markdown_content = _html_to_markdown(html_content)
            
            # 清理多余空行
            import re
            markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
            
            # 长度限制保护
            MAX_LEN = 4000
            if len(markdown_content) > MAX_LEN:
                logger.warning(f"内容超长 ({len(markdown_content)}), 已截断")
                return (
                    f"【系统反馈】内容已自动截取前 {MAX_LEN} 字：\n\n"
                    f"{markdown_content[:MAX_LEN]}..."
                )
            
            return markdown_content

    except Exception as e:
        logger.error(f"异步读取网页失败: {e}")
        from tools.tools_common import format_error_payload
        return format_error_payload(
            "read_webpage_content",
            str(e),
            "尝试使用 tavilySearch 获取更准确的摘要"
        )
