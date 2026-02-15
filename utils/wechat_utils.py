import winreg
import os
from pathlib import Path
from utils.logger import logger

def get_wechat_file_root():
    """
    从注册表读取微信文件存储根路径。
    默认通常在 C:\\Users\\[User]\\Documents\\WeChat Files
    用户可能修改为自定义路径，如 E:\\WeChat Files
    """
    try:
        # 打开注册表项
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat", 0, winreg.KEY_READ)
        try:
            path_val, _ = winreg.QueryValueEx(key, "FileSavePath")
        except:
            path_val = None
        winreg.CloseKey(key)
        
        if path_val:
            if path_val == "MyDocuments:":
                return os.path.join(os.path.expanduser("~"), "Documents", "WeChat Files")
            return os.path.join(path_val, "WeChat Files")
    except Exception as e:
        logger.warning(f"无法从注册表获取 WeChat 路径: {e}")
    
    # 启发式检查常见路径
    possible_roots = [
        "E:\\WeChat Files",
        "E:\\OneDrive - MSFT\\WeChat Files",
        os.path.join(os.path.expanduser("~"), "Documents", "WeChat Files")
    ]
    for root in possible_roots:
        if os.path.exists(root):
            return root
            
    return possible_roots[-1]

def find_latest_voice_file(wx_root, scout_seconds=30):
    """
    [旧版保留] 在微信根目录下寻找最新的语音文件 (silk/amr)。
    出于兼容性保留，但在 v11.0 中推荐优先使用 fast_scan_voice_file。
    """
    if not os.path.exists(wx_root):
        return None
    return fast_scan_voice_file(wx_root, scout_seconds)

def fast_scan_voice_file(wx_root: str, scout_seconds: int = 15) -> str | None:
    """
    [v11.0 物理解封] 使用原生 shell 命令极速定位最新语音文件。
    绕过 Python os.walk 的缓慢遍历，直接利用 Windows dir 索引。
    """
    if not os.path.exists(wx_root):
        logger.error(f"微信根目录不存在: {wx_root}")
        return None

    import subprocess
    import time
    
    logger.info(f"🔍 [Scanner] 启动物理解封雷达，目标: {wx_root}")
    
    # 锁定 FileStorage/Voice 路径模式
    # 使用 dir /S /B /O-D 按照时间逆序快速列出所有 .silk 文件
    try:
        # 强制 UTF-8 环境以支持中文路径探测
        cmd = f'chcp 65001 >nul && dir "{wx_root}\\*FileStorage\\Voice\\*.silk" /S /B /O-D'
        result = subprocess.check_output(cmd, shell=True, encoding='utf-8', errors='ignore')
        
        lines = [line.strip() for line in result.split("\n") if line.strip() and line.endswith(".silk")]
        
        if not lines:
            logger.warning("未能在物理路径发现任何 .silk 文件")
            return None
            
        # 验证最新文件的时间戳是否在范围内
        latest_file = lines[0]
        if os.path.exists(latest_file):
            mtime = os.path.getmtime(latest_file)
            if (time.time() - mtime) < scout_seconds:
                logger.info(f"✅ [Scanner] 成功捕获物理残留: {latest_file} (offset: {int(time.time() - mtime)}s)")
                return latest_file
            else:
                logger.debug(f"最新文件过于陈旧 ({int(time.time() - mtime)}s前)，忽略")
                
    except Exception as e:
        logger.debug(f"物理扫描过程提示: {e} (通常是因为目录下没有匹配文件)")
        
    return None
