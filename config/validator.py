"""
配置验证模块

提供配置项的验证、默认值设置和错误报告功能。
"""
import os
from pathlib import Path
from typing import List, Dict, Any
from utils.logger import logger

class ConfigValidator:
    """配置验证器"""
    
    def __init__(self, settings: Any):
        self.settings = settings
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_all(self) -> bool:
        """验证所有配置项"""
        self.errors.clear()
        self.warnings.clear()
        
        # 验证API密钥
        self._validate_api_keys()
        
        # 验证路径配置
        self._validate_paths()
        
        # 验证数值配置
        self._validate_numeric_values()
        
        # 验证微信配置
        self._validate_wechat_config()
        
        # 输出验证结果
        if self.errors:
            logger.error("配置验证失败，存在以下错误:")
            for error in self.errors:
                logger.error(f"  - {error}")
            return False
            
        if self.warnings:
            logger.warning("配置验证警告:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
                
        logger.info("配置验证通过")
        return True
        
    def _validate_api_keys(self):
        """验证API密钥配置"""
        provider = getattr(self.settings, 'llm_provider', 'google').lower()
        
        if provider == 'google' and not self.settings.google_api_key:
            self.errors.append("GOOGLE_API_KEY 未配置，Google AI服务将无法使用")
        elif provider == 'openai' and not self.settings.openai_api_key:
            self.errors.append("OPENAI_API_KEY 未配置，OpenAI服务将无法使用")
        elif provider == 'anthropic' and not self.settings.anthropic_api_key:
            self.errors.append("ANTHROPIC_API_KEY 未配置，Anthropic服务将无法使用")
        elif provider == 'deepseek' and not self.settings.deepseek_api_key:
            self.errors.append("DEEPSEEK_API_KEY 未配置，DeepSeek服务将无法使用")
        elif provider == 'qwen' and not self.settings.qwen_api_key:
            self.errors.append("QWEN_API_KEY 未配置，千问AI服务将无法使用")
            
        if not self.settings.tavily_api_key:
            self.warnings.append("TAVILY_API_KEY 未配置，将使用浏览器搜索替代")
            
    def _validate_paths(self):
        """验证路径配置"""
        try:
            # 验证项目根目录
            project_root = self.settings.project_root
            if not project_root.exists():
                self.errors.append(f"项目根目录不存在: {project_root}")
                
            # 验证数据库路径
            db_path = self.settings.db_full_path
            db_dir = db_path.parent
            if not db_dir.exists():
                try:
                    db_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"已创建数据库目录: {db_dir}")
                except Exception as e:
                    self.errors.append(f"无法创建数据库目录 {db_dir}: {e}")
                    
            # 验证日志目录
            log_dir = self.settings.log_full_dir
            if not log_dir.exists():
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"已创建日志目录: {log_dir}")
                except Exception as e:
                    self.errors.append(f"无法创建日志目录 {log_dir}: {e}")
                    
        except Exception as e:
            self.errors.append(f"路径验证异常: {e}")
            
    def _validate_numeric_values(self):
        """验证数值配置"""
        # 验证温度值
        if not (0.0 <= self.settings.temperature <= 1.0):
            self.warnings.append(f"temperature 值 {self.settings.temperature} 超出推荐范围 [0.0, 1.0]")
            
        # 验证最大输出token数
        if self.settings.max_output_tokens <= 0:
            self.errors.append("max_output_tokens 必须大于0")
            
        # 验证内存窗口大小
        if self.settings.memory_window_size <= 0:
            self.warnings.append("memory_window_size 应该大于0以启用对话记忆")
            
        # 验证重试次数
        if self.settings.max_retries < 0:
            self.errors.append("max_retries 不能为负数")
            
    def _validate_wechat_config(self):
        """验证微信配置"""
        if not self.settings.master_remark:
            self.errors.append("MASTER_REMARK 未配置，无法识别主人身份")
            
        if not self.settings.whitelist:
            self.warnings.append("微信白名单为空，将不会处理任何消息")
            
        # 验证监听间隔
        if self.settings.listen_interval <= 0:
            self.warnings.append("listen_interval 应该大于0")
            
        # 验证回复延迟
        if self.settings.reply_delay_min < 0 or self.settings.reply_delay_max < 0:
            self.errors.append("回复延迟时间不能为负数")
            
        if self.settings.reply_delay_min > self.settings.reply_delay_max:
            self.errors.append("reply_delay_min 不能大于 reply_delay_max")

def validate_configuration(settings: Any) -> bool:
    """
    验证配置并返回结果
    
    Args:
        settings: 配置对象
        
    Returns:
        bool: 验证是否通过
    """
    validator = ConfigValidator(settings)
    return validator.validate_all()