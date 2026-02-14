"""
浏览器操作工具

使用 Playwright Headless 模式访问网页，
提取页面文本内容供 AI Agent 分析。

NOTE: 此工具是 searchWeb 的下游工具，
典型流程为 searchWeb -> browseWebpage -> 总结回复。
"""
from langchain_core.tools import tool

from core.config import conf
from utils.logger import logger


@tool
async def browseWebpage(url: str, actions: list[dict] = None) -> str:
    """
    [v8.0 Operator] 智能交互式网页浏览器。
    支持在访问页面后执行一系列动作（如点击、输入、滚动等）。
    
    Args:
        url: 目标网页 URL。
        actions: (可选) 动作列表。示例: 
            [
                {"type": "click", "selector": "text=搜索"}, 
                {"type": "fill", "selector": "#keyword", "text": "击剑"},
                {"type": "press", "key": "Enter"},
                {"type": "wait", "ms": 2000}
            ]
    """
    # 🚨 强制修复并清洗 URL (Fixing Protocol and Whitespace)
    url = url.strip()
    if not url.startswith('http'):
        url = 'https://' + url
    
    logger.info(f"🌍 [Operator] 正在探索: {url}")
    if actions:
        import json
        logger.info(f"🎮 [Operator] 计划执行动作: {json.dumps(actions, ensure_ascii=False)}")

    try:
        from playwright.async_api import async_playwright
        import html2text

        # 优化 HTML 转 Text 的配置
        h = html2text.HTML2Text()
        h.ignore_links = False  # 保留链接，让 AI 看到哪里可以点
        h.ignore_images = True
        h.body_width = 0
        h.ignore_emphasis = True

        async with async_playwright() as p:
            # 启动配置：伪装成高版本 Chrome
            browser = None
            try:
                browser = await p.chromium.launch(headless=True)
            except Exception as launch_err:
                if "Executable doesn't exist" in str(launch_err):
                    logger.warning("默认 Chromium 未找到，尝试使用系统 Edge.")
                    browser = await p.chromium.launch(headless=True, channel="msedge")
                else:
                    raise launch_err

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            try:
                # 1. 访问页面
                await page.goto(url, timeout=45000, wait_until="domcontentloaded")
                await page.wait_for_timeout(1000)

                # 2. [核心] 执行动作流
                if actions:
                    for i, act in enumerate(actions):
                        act_type = act.get("type")
                        selector = act.get("selector")
                        try:
                            if act_type == "click":
                                logger.info(f"   👉 点击: {selector}")
                                await page.click(selector, timeout=8000)
                            elif act_type == "fill":
                                text = act.get("text", "")
                                logger.info(f"   ⌨️ 输入: {selector} -> {text}")
                                await page.fill(selector, text, timeout=5000)
                            elif act_type == "press":
                                key = act.get("key", "Enter")
                                logger.info(f"   ↵ 按键: {key}")
                                await page.keyboard.press(key)
                            elif act_type == "wait":
                                ms = act.get("ms", 1000)
                                logger.debug(f"   ⏳ 等待: {ms}ms")
                                await page.wait_for_timeout(ms)
                            
                            # 动作间歇，给页面响应时间
                            await page.wait_for_timeout(800)
                        except Exception as action_err:
                            logger.warning(f"   ⚠️ 动作 {i+1} ({act_type}) 失败: {action_err}")

                # 3. [SPA 核心] 智能等待数据加载
                logger.debug("⏳ 等待页面数据最终渲染 (networkidle)...")
                try:
                    await page.wait_for_load_state("networkidle", timeout=8000)
                except:
                    pass

                # 4. 滚动页面 (触发懒加载)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500) 

                # 5. [关键] 提取可交互链接和元素
                links_summary = await page.evaluate("""() => {
                    const elements = Array.from(document.querySelectorAll('a[href], button, [role="button"]'));
                    return elements
                        .filter(el => {
                            const text = el.innerText.trim();
                            return text.length > 2;
                        })
                        .slice(0, 40)
                        .map(el => `[元素] ${el.innerText.trim().replace(/\\n/g, ' ')} (Ref: ${el.href || 'button'})`)
                        .join('\\n');
                }""")

            except Exception as e:
                if browser: await browser.close()
                return f"【系统反馈】操作中断: {str(e)}。无法完成动作流或页面加载。"

            # 获取内容
            html = await page.content()
            title = await page.title()
            await browser.close()

            # 转换为 Markdown
            text_content = h.handle(html)
            
            # 5. 组装最终报告：保留核心数据，移除诱导性操作标题
            max_length = conf.browse_max_content_length
            report = (
                f"--- 网页数据抓取成功: {title} ---\n"
                f"{text_content[:max_length]}\n\n"
                f"--- 可读链接/元素 ---\n{links_summary}"
            )
            
            return report

    except Exception as e:
        logger.error(f"Operator 浏览器崩溃: {e}")
        return f"【系统反馈】浏览器核心崩溃: {str(e)}"
