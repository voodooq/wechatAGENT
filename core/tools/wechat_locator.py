import os
import winreg
import subprocess
from pathlib import Path
from langchain_core.tools import tool
from utils.logger import logger

@tool
def ultra_wechat_locator() -> str:
    """
    [雷达] 终极微信路径探测器 (v11.0)。支持：
    1. 自动解析注册表 MyDocuments: 占位符。
    2. 跨盘符深度扫描 WeChat Files。
    3. 精准锁定活跃用户 MsgAttach 物理存放路径。
    """
    try:
        storage_path = ""
        # 1. 从注册表读取微信文件存储根目录
        reg_path = r"Software\Tencent\WeChat"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                storage_path, _ = winreg.QueryValueEx(key, "FileSavePath")
        except Exception as e:
            logger.warning(f"注册表读取失败: {e}")

        # 2. 解析 MyDocuments: 占位符
        if "MyDocuments:" in storage_path:
            # 使用 PowerShell 获取标准的‘文档’物理路径，确保编码正确
            shell_cmd = 'powershell -NoProfile -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; [Environment]::GetFolderPath(\'MyDocuments\')"'
            doc_path = subprocess.check_output(shell_cmd, shell=True, encoding='utf-8').strip()
            base_path = storage_path.replace("MyDocuments:", doc_path)
        else:
            base_path = storage_path if storage_path.strip() else os.path.join(os.environ["USERPROFILE"], "Documents", "WeChat Files")

        # 3. 扫描具体的 ID 目录并定位 MsgAttach
        wx_root = Path(base_path)
        if "WeChat Files" not in str(wx_root):
            wx_root = wx_root / "WeChat Files"
            
        if not wx_root.exists():
            # [v11.0 增强] 跨盘符雷达扫描
            logger.info(f"路径 {wx_root} 不存在，启动跨盘符扫描...")
            for drive in ["D:", "E:", "F:", "C:"]:
                potential = Path(f"{drive}/WeChat Files")
                if potential.exists():
                    wx_root = potential
                    break

        if not wx_root.exists():
            return "❌ 路径探测失败：未能找到微信存档根目录。"

        # 寻找包含 FileStorage 的用户文件夹（排除 All Users）
        user_dirs = [d for d in wx_root.iterdir() if d.is_dir() and d.name != "All Users" and (d / "FileStorage").exists()]
        if not user_dirs:
            return f"❌ 定位失败：在 {wx_root} 未发现活跃用户数据。"

        # 锁定最近修改的用户目录
        active_user = max(user_dirs, key=lambda d: d.stat().st_mtime)
        target = active_user / "FileStorage" / "MsgAttach"
        
        logger.info(f"🧬 [Omni-Path] v11.0 成功锁定: {target}")
        return str(target.absolute())

    except Exception as e:
        logger.error(f"❌ 路径探测异常: {str(e)}")
        return f"❌ 探测异常: {str(e)}"
