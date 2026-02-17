import os
import winreg
import json
from pathlib import Path
from typing import Optional, Dict, List
from langchain_core.tools import tool
from utils.logger import logger

class IMVoiceLocator:
    """通用IM语音文件定位器"""
    
    def __init__(self):
        self.supported_ims = {
            'wechat': self._locate_wechat_voice,
            'qq': self._locate_qq_voice,
            'dingtalk': self._locate_dingtalk_voice,
            'lark': self._locate_lark_voice,
            'telegram': self._locate_telegram_voice
        }
    
    def locate_voice_path(self, im_type: str, scout_seconds: int = 30) -> Optional[str]:
        """
        定位指定IM软件的最新语音文件
        
        Args:
            im_type: IM类型 ('wechat', 'qq', 'dingtalk', 'lark', 'telegram')
            scout_seconds: 扫描时间范围（秒）
            
        Returns:
            最新语音文件路径，如果未找到则返回None
        """
        if im_type not in self.supported_ims:
            logger.warning(f"不支持的IM类型: {im_type}")
            return None
            
        try:
            locator_func = self.supported_ims[im_type]
            return locator_func(scout_seconds)
        except Exception as e:
            logger.error(f"{im_type}语音定位失败: {e}")
            return None
    
    def _locate_wechat_voice(self, scout_seconds: int) -> Optional[str]:
        """定位微信语音文件"""
        from core.tools.wechat_locator import ultra_wechat_locator
        from utils.wechat_utils import fast_scan_voice_file
        
        # 获取微信锚点
        anchor_result = ultra_wechat_locator.invoke({})
        if "❌" in anchor_result:
            logger.error(f"微信锚点定位失败: {anchor_result}")
            return None
            
        # 扫描语音文件
        voice_path = fast_scan_voice_file(anchor_result, scout_seconds)
        return voice_path
    
    def _locate_qq_voice(self, scout_seconds: int) -> Optional[str]:
        """定位QQ语音文件"""
        import time
        from pathlib import Path
        
        # QQ语音文件通常存储在以下位置
        possible_roots = [
            os.path.join(os.environ.get('APPDATA', ''), 'Tencent', 'QQ', 'Audio'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'Tencent Files'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Tencent', 'QQ', 'Audio')
        ]
        
        # 也尝试从注册表获取QQ安装路径
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Tencent\QQ") as key:
                install_path, _ = winreg.QueryValueEx(key, "Install")
                if install_path:
                    possible_roots.append(os.path.join(install_path, "Audio"))
        except (OSError, FileNotFoundError):
            pass
        
        return self._scan_voice_files(possible_roots, scout_seconds, ['.silk', '.amr', '.mp3', '.m4a'])
    
    def _locate_dingtalk_voice(self, scout_seconds: int) -> Optional[str]:
        """定位钉钉语音文件"""
        import time
        from pathlib import Path
        
        # 钉钉语音文件位置
        possible_roots = [
            os.path.join(os.environ.get('APPDATA', ''), 'DingTalk', 'Audio'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'DingTalk', 'Audio'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'DingTalk')
        ]
        
        return self._scan_voice_files(possible_roots, scout_seconds, ['.amr', '.mp3', '.m4a', '.wav'])
    
    def _locate_lark_voice(self, scout_seconds: int) -> Optional[str]:
        """定位飞书语音文件"""
        import time
        from pathlib import Path
        
        # 飞书语音文件位置
        possible_roots = [
            os.path.join(os.environ.get('APPDATA', ''), 'Lark', 'Audio'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Lark', 'Audio'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'Lark')
        ]
        
        return self._scan_voice_files(possible_roots, scout_seconds, ['.mp3', '.m4a', '.wav', '.ogg'])
    
    def _locate_telegram_voice(self, scout_seconds: int) -> Optional[str]:
        """定位Telegram语音文件"""
        import time
        from pathlib import Path
        
        # Telegram语音文件位置
        possible_roots = [
            os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads', 'Telegram Desktop'),
            os.path.join(os.environ.get('APPDATA', ''), 'Telegram Desktop', 'tdata'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Telegram Desktop', 'tdata')
        ]
        
        return self._scan_voice_files(possible_roots, scout_seconds, ['.oga', '.ogg', '.mp3', '.m4a'])
    
    def _scan_voice_files(self, roots: List[str], scout_seconds: int, extensions: List[str]) -> Optional[str]:
        """通用语音文件扫描函数"""
        import time
        from pathlib import Path
        
        now = time.time()
        latest_file = None
        latest_time = 0
        
        for root in roots:
            root_path = Path(root)
            if not root_path.exists():
                continue
                
            try:
                for file_path in root_path.rglob('*'):
                    if file_path.is_file():
                        if any(file_path.suffix.lower() == ext for ext in extensions):
                            mtime = file_path.stat().st_mtime
                            if mtime > latest_time and (now - mtime) < scout_seconds:
                                latest_time = mtime
                                latest_file = str(file_path)
            except (PermissionError, OSError) as e:
                logger.debug(f"扫描目录 {root} 时权限错误: {e}")
                continue
        
        if latest_file:
            logger.info(f"✅ 找到最新语音文件: {latest_file}")
        else:
            logger.warning(f"❌ 在指定时间内未找到语音文件")
            
        return latest_file

# 全局实例
_im_locator = IMVoiceLocator()

@tool
def locate_im_voice(im_type: str, scout_seconds: int = 30) -> str:
    """
    [多IM支持] 定位指定IM软件的最新语音文件路径。
    
    支持的IM类型: wechat, qq, dingtalk, lark, telegram
    
    Args:
        im_type: IM类型
        scout_seconds: 扫描时间范围（秒），默认30秒
        
    Returns:
        语音文件路径或错误信息
    """
    result = _im_locator.locate_voice_path(im_type, scout_seconds)
    if result:
        return result
    else:
        return f"❌ 未能在{scout_seconds}秒内找到{im_type}的语音文件"

@tool  
def get_supported_im_types() -> str:
    """
    [多IM支持] 获取支持的IM类型列表。
    
    Returns:
        支持的IM类型列表
    """
    supported = ['wechat', 'qq', 'dingtalk', 'lark', 'telegram']
    return f"支持的IM类型: {', '.join(supported)}"