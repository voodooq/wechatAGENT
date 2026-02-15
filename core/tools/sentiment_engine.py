from langchain_core.tools import tool
from utils.logger import logger

@tool
def analyze_voice_sentiment(transcript: str, duration: float) -> str:
    """
    [情感分析] 根据转录内容和音频时长，计算情绪倾向。
    返回一个情绪标签供大脑参考。
    """
    try:
        # 1. 计算语速 (字符/秒)
        char_count = len(transcript)
        # 微信语音时长通常准确
        wps = char_count / duration if duration > 0.1 else 0
        
        # 2. 基于关键词的情绪初筛
        happy_keywords = ["开心", "好棒", "太好了", "哈哈", "喜", "棒"]
        urgent_keywords = ["快点", "急", "马上", "速度", "等不了", "赶"]
        angry_keywords = ["烦", "气", "怎么回事", "搞什么", "差", "讨厌"]
        
        sentiment = "NEUTRAL"
        
        # 3. 混合分析逻辑
        if any(kw in transcript for kw in happy_keywords):
            sentiment = "HAPPY"
        elif any(kw in transcript for kw in urgent_keywords) or wps > 4.5:
            sentiment = "URGENT"
        elif any(kw in transcript for kw in angry_keywords):
            sentiment = "ANGRY"
        elif wps < 1.0 and char_count > 2:
            sentiment = "HESITANT"

        logger.info(f"🎭 [Sentiment] 转录内容: {transcript} | 语速: {wps:.2f} | 识别情绪: {sentiment}")
        
        # 返回增强用的 Prompt 提示词片段
        strategies = {
            "HAPPY": "用户目前心情很愉快。请在回复中表现出同样的活力，可以使用表情符号如 🌟, 🚀。",
            "URGENT": "用户状态非常急迫。请跳过寒暄，直接提供最精简、最高效的结论，字数减少 50% 以上。",
            "ANGRY": "用户情绪带有不满或愤怒。请保持极致的专业度与中立性，优先确认并解决其痛点，避免任何俏皮话。",
            "HESITANT": "用户表现得有些犹豫或困惑。请回复得更加详细、耐心，提供分步指引。",
            "NEUTRAL": "用户情绪平稳。请保持你作为 IT 专家的标准专业回复风格。"
        }
        
        return f"[情感感知结果: {sentiment}] {strategies.get(sentiment, '')}"

    except Exception as e:
        logger.error(f"情感引擎异常: {e}")
        return "[情感感知结果: UNKNOWN] 保持常规专业风格即可。"
