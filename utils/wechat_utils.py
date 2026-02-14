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

def find_latest_voice_file(wx_root, sender_name=None):
    """
    在微信根目录下寻找最新的语音文件 (silk/amr)。
    由于 wxid 目录名称通常是模糊的，我们会扫描整个 WeChat Files 下的所有 FileStorage/Voice 目录。
    """
    if not os.path.exists(wx_root):
        logger.error(f"微信根目录不存在: {wx_root}")
        return None

    logger.info(f"🔍 正在从微信根目录检索语音: {wx_root}")
    
    # 查找所有 FileStorage/Voice 结尾的目录
    voice_dirs = []
    for root, dirs, files in os.walk(wx_root):
        if root.endswith(os.path.join("FileStorage", "Voice")):
            voice_dirs.append(root)
            # 限制扫描深度，防止太慢
            if len(voice_dirs) > 20: break 

    if not voice_dirs:
        logger.warning("未找到任何语音存储目录 (FileStorage/Voice)")
        return None

    latest_file = None
    latest_time = 0

    # 在所有语音目录中找最新的文件
    for d in voice_dirs:
        try:
            for f in os.listdir(d):
                if f.endswith(('.silk', '.amr', '.wav')):
                    f_path = os.path.join(d, f)
                    f_time = os.path.getmtime(f_path)
                    if f_time > latest_time:
                        latest_time = f_time
                        latest_file = f_path
        except: continue

    # 检查文件是否是最近生成的（比如 10 秒内）
    import time
    if latest_file and (time.time() - latest_time) < 30:
        logger.info(f"✅ 成功定位到最新产生的语音文件: {latest_file}")
        return latest_file
    
    logger.warning("未能找到最近 30 秒内生成的语音文件")
    return None
