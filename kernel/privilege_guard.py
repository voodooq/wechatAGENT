import os
import ctypes
import sys
from utils.logger import logger

def is_admin():
    """检查当前是否具备管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    """如果不具备管理员权限，尝试提升权限并重启系统"""
    if is_admin():
        logger.info("✅ 当前已处于管理员模式。")
        return True
    
    logger.warning("⚠️ 检测到权限不足，正在尝试申请管理员权限...")
    
    # 重新以管理员身份运行当前脚本
    # ShellExecuteW 参数：hwnd, operation, file, parameters, directory, showCmd
    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        if ret > 32:
            logger.info("🚀 提权请求已发送，请在弹窗中确认。系统将自动重启。")
            sys.exit(0)
        else:
            logger.error(f"❌ 提权失败，返回码: {ret}")
            return False
    except Exception as e:
        logger.error(f"❌ 提权过程异常: {e}")
        return False
