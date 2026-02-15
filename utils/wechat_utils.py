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

def fast_scan_voice_file(anchor_path: str, scout_seconds: int = 15) -> str | None:
    """
    [v11.8 Precision-Hunter] 使用 Python 原生 os.walk 极速深度搜索。
    针对 Voice 文件夹进行深度收割，校准锚点偏移。
    """
    if not os.path.exists(anchor_path):
        logger.error(f"❌ 物理锚点不存在: {anchor_path}")
        return None

    import time
    from pathlib import Path
    
    # 锚点校准：从 MsgAttach 或 FileStorage 锚点转向真正的 Voice 目录
    anchor = Path(anchor_path)
    if anchor.name == "MsgAttach":
        voice_root = anchor.parent / "Voice"
    elif anchor.name == "FileStorage":
        voice_root = anchor / "Voice"
    else:
        # 如果锚点是 ID 目录或其他，尝试直接寻找
        voice_root = anchor / "FileStorage" / "Voice"
    
    if not voice_root.exists():
        logger.warning(f"⚠️ [Scanner] 找不到 Voice 目录，尝试在锚点全量递归: {anchor_path}")
        voice_root = anchor

    logger.info(f"🔍 [Precision-Hunter] 启动深度捕获，根目录: {voice_root}")

    latest_file = None
    latest_time = 0
    now = time.time()
    
    # [v11.8] 使用 os.walk 进行深度探测，因为语音文件深度不固定 (年份-月份/哈希/xxxx.silk)
    try:
        for root, _, files in os.walk(voice_root):
            for f in files:
                if f.lower().endswith(('.silk', '.aud')):
                    f_path = os.path.join(root, f)
                    mtime = os.path.getmtime(f_path)
                    if mtime > latest_time and (now - mtime) < scout_seconds:
                        latest_time = mtime
                        latest_file = f_path
                    
        if latest_file:
            logger.info(f"✅ [Precision-Hunter] 成功收割物理残留: {latest_file} ({int(now - latest_time)}s offset)")
            return latest_file
            
    except Exception as e:
        logger.debug(f"物理扫描过程提示: {e}")
        
    return None
