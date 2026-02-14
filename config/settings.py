"""
全局配置管理

通过 .env 文件和环境变量加载配置项，
提供统一的配置访问接口。
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List
from dotenv import load_dotenv

# NOTE: 项目根目录基于此文件所在位置推算
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 加载 .env 文件
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class Settings:
    """全局配置类，集中管理所有可调参数"""

    # === API Keys ===
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")

    # === 代理配置 ===
    # 注意：如果留空则使用系统默认或无代理
    https_proxy: Optional[str] = os.getenv("HTTPS_PROXY")
    http_proxy: Optional[str] = os.getenv("HTTP_PROXY")

    # === AI 模型配置 ===
    model_name: str = os.getenv("MODEL_NAME", "gemini-2.5-flash")
    temperature: float = 0.7
    max_output_tokens: int = 2048
    # Gemini 2.5 Pro RPM Limit (Default: 15)
    genai_rpm: int = 15

    # === 对话记忆 ===
    # 每个联系人保留的历史消息轮数
    memory_window_size: int = 10

    # === 微信配置 ===
    master_wxid: str = os.getenv("MASTER_WXID", "")  # 主人的唯一微信号 (WxID, 如 voodooq)
    master_remark: str = os.getenv("MASTER_REMARK", "文件传输助手")
    # 白名单（字符串形式，逗号分隔，内部会自动解析为 list）
    _whitelist_str: str = os.getenv("WHITELIST", "文件传输助手")
    whitelist: list[str] = field(default_factory=list)
    # 消息轮询间隔（秒）
    listen_interval: float = 1.0

    # === 防风控配置 ===
    # 回复延迟范围（秒），随机取值
    reply_delay_min: float = 2.0
    reply_delay_max: float = 5.0
    # 单条消息最大长度，超出则分段发送
    max_message_length: int = 500
    # AI 消息签名后缀，用于标识机器人回复并防止回环
    ai_signature: str = os.getenv("AI_SIGNATURE", " (AI)")

    # === 每日摘要 ===
    # 摘要触发时间 (24h 格式)
    summary_time: str = "23:00"
    # 摘要接收人
    summary_receiver: str = "文件传输助手"

    # === 数据库 ===
    db_path: str = os.getenv("DB_PATH", "data/work.db")

    # === 日志 ===
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: str = "logs"
    daily_log_dir: str = "logs/daily"

    # === 稳定性 ===
    # 异常重试次数
    max_retries: int = 3
    # 重试间隔（秒）
    retry_delay: float = 5.0
    # 微信窗口保活检查间隔（秒）
    keepalive_interval: float = 60.0

    # === Agent 行为 ===
    # Agent 最大推理步骤数（支持多步链式操作）
    agent_max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
    # 网页内容最大提取长度（字符数）
    browse_max_content_length: int = int(os.getenv("BROWSE_MAX_CONTENT_LENGTH", "5000"))

    def __post_init__(self):
        """环境变量加载后的后处理逻辑"""
        # 1. 处理白名单字符串
        if hasattr(self, '_whitelist_str') and self._whitelist_str:
            items = [item.strip() for item in self._whitelist_str.split(",") if item.strip()]
            for item in items:
                if item not in self.whitelist:
                    self.whitelist.append(item)
        
        # 2. 确保主人备注名一定在白名单中
        if self.master_remark and self.master_remark not in self.whitelist:
            self.whitelist.append(self.master_remark)
            
        # 3. 初始白名单去重
        self.whitelist = list(set(self.whitelist))

        # 4. 注入代理环境变量 (确保 requests, httpx 等库生效)
        # [稳定性修复] 强制将 socks5(h) 修改为 http，以适配 gRPC (Gemini SDK)
        def fix_proxy(url: Optional[str]) -> Optional[str]:
            if not url: return None
            if url.startswith("socks5"):
                new_url = url.replace("socks5h://", "http://").replace("socks5://", "http://")
                import logging
                logging.getLogger("ai_assistant").warning(f"检测到 gRPC 不支持的代理协议，已自动从 {url} 修正为 {new_url}")
                return new_url
            return url

        final_https = fix_proxy(self.https_proxy)
        final_http = fix_proxy(self.http_proxy)

        if final_https:
            os.environ["HTTPS_PROXY"] = final_https
            os.environ["https_proxy"] = final_https
        if final_http:
            os.environ["HTTP_PROXY"] = final_http
            os.environ["http_proxy"] = final_http
        
        # 额外注入 gRPC 可能需要的变量
        if final_https:
             os.environ["GRPC_PROXY_EXP"] = final_https

    @property
    def project_root(self) -> Path:
        """获取项目根目录"""
        return PROJECT_ROOT
        
    @property
    def PROJECT_ROOT(self) -> Path:
        """获取项目根目录 (兼容旧代码)"""
        return PROJECT_ROOT

    @property
    def db_full_path(self) -> Path:
        """获取数据库绝对路径"""
        return PROJECT_ROOT / self.db_path

    @property
    def log_full_dir(self) -> Path:
        """获取日志目录绝对路径"""
        return PROJECT_ROOT / self.log_dir

    @property
    def daily_log_full_dir(self) -> Path:
        """获取每日日志目录绝对路径"""
        return PROJECT_ROOT / self.daily_log_dir

    def validate(self) -> list[str]:
        """
        验证关键配置项是否已设置

        Returns:
            缺失配置项的警告信息列表
        """
        warnings: list[str] = []
        if not self.google_api_key:
            warnings.append("GOOGLE_API_KEY 未设置，AI Agent 将无法工作")
        if not self.tavily_api_key:
            warnings.append("TAVILY_API_KEY 未设置，将使用浏览器搜索替代")
        if not self.master_remark:
            warnings.append("MASTER_REMARK 未设置，无法识别主人身份")
        if not self.whitelist:
            warnings.append("微信白名单为空，将不会处理任何消息")
        return warnings


# 全局单例
settings = Settings()
