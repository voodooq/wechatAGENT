"""
IronSentinel 内核模块
"""

from .tools import *

# 语音处理相关
try:
    from core.tools.voice_tools import process_voice_message, auto_detect_voice_messages
    __all__ = ['process_voice_message', 'auto_detect_voice_messages'] + tools.__all__
except ImportError:
    __all__ = tools.__all__