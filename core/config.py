"""
IronSentinel 核心配置
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
VOICE_MESSAGES_DIR = DATA_DIR / "voice_messages"

# 确保目录存在
for directory in [DATA_DIR, VOICE_MESSAGES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 语音处理配置
VOICE_CONFIG = {
    "enabled": True,
    "supported_formats": [".silk", ".amr", ".mp3", ".m4a", ".wav"],
    "max_file_age_hours": 24,
    "auto_cleanup": True
}

# 数据库配置
DATABASE_PATH = DATA_DIR / "work.db"

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": DATA_DIR / "iron_sentinel.log"
}