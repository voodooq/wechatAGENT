import os
import winreg
import subprocess
from pathlib import Path
from langchain_core.tools import tool
from utils.logger import logger

@tool
def ultra_wechat_locator() -> str:
    """
    [雷达] 终极微信路径探测器 (v10.9)。支持：
    1. 自动解析注册表 MyDocuments: 占位符。
    2. 跨盘符 (C/D/E/F) 根目录扫描 WeChat Files。
    3. 获取 MsgAttach 物理存放路径。
    """
    try:
        storage_path = ""
        # 1. 优先探测注册表
        reg_path = r"Software\Tencent\WeChat"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                storage_path, _ = winreg.QueryValueEx(key, "FileSavePath")
        except: pass

        # 2. 解析占位符 (彻底解决系统账户差异：Administrator vs Lenove)
        if "MyDocuments:" in storage_path:
            cmd = 'powershell -NoProfile -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; [Environment]::GetFolderPath(\'MyDocuments\')"'
            doc_path = subprocess.check_output(cmd, shell=True, encoding='utf-8').strip()
            storage_path = storage_path.replace("MyDocuments:", doc_path)
        
        # 3. 路径合法性验证与回退
        wx_root = Path(storage_path) / "WeChat Files" if storage_path else None
        
        if not wx_root or not wx_root.exists():
            # [v10.9 增强] 跨盘符深度扫描
            logger.info("注册表定位失效，启动跨盘符雷达扫描...")
            for drive in ["D:", "E:", "F:", "C:"]:
                potential = Path(f"{drive}/WeChat Files")
                if potential.exists():
                    wx_root = potential
                    break
        
        if not wx_root or not wx_root.exists():
            # 最后的尝试：当前用户目录
            wx_root = Path(os.environ["USERPROFILE"]) / "Documents" / "WeChat Files"
            if not wx_root.exists():
                return "❌ 路径探测失败：未能找到微信存档根目录。"

        # 4. 定位活跃用户 MsgAttach 目录
        candidates = [d for d in wx_root.iterdir() if d.is_dir() and (d / "FileStorage").exists()]
        if not candidates:
            return f"❌ 定位失败：在 {wx_root} 未发现用户数据。"
            
        active_user = max(candidates, key=lambda d: d.stat().st_mtime)
        target = active_user / "FileStorage" / "MsgAttach"
        
        logger.info(f"🧬 [Omni-Path] 成功锁定: {target}")
        return str(target.absolute())

    except Exception as e:
        logger.error(f"❌ 路径探测异常: {str(e)}")
        return f"❌ 探测异常: {str(e)}"
