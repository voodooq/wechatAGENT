class ConfigTemplate:
    """
    公开配置模板 (不含敏感信息)
    """
    # API 密钥
    llm_provider = "google" # google, openai, anthropic, deepseek, openai-compatible
    google_api_key = ""
    openai_api_key = ""
    openai_api_base = "https://api.openai.com/v1"
    anthropic_api_key = ""
    deepseek_api_key = ""
    deepseek_api_base = "https://api.deepseek.com"
    tavily_api_key = ""
    
    # 代理
    https_proxy = ""
    http_proxy = ""
    
    # 模型
    model_name = "gemini-2.0-flash"
    temperature = 0.2
    max_output_tokens = 2048
    genai_rpm = 15
    
    # 微信与行为
    master_wxid = "voodooq"
    master_remark = "文件传输助手"
    whitelist = ["文件传输助手"]
    ai_signature = " [IronSentinel v10.0]"
    
    # 路径与系统
    db_path = "data/work.db"
    log_level = "INFO"
    agent_max_iterations = 15
    browse_max_content_length = 5000
    reply_delay_min = 2.0
    reply_delay_max = 5.0
    max_message_length = 500
    listen_interval = 1.0
    
    # 语音功能增强 (TTS)
    tts_enabled = False
    tts_provider = "edge"
    tts_voice = "zh-CN-XiaoxiaoNeural"
    tts_local_play = True
    tts_send_to_chat = False
    
    # 摘要与记忆
    summary_time = "22:00"
    summary_receiver = "文件传输助手"
    memory_window_size = 10
    
    # 稳定性
    retry_delay = 5.0
    max_retries = 3
