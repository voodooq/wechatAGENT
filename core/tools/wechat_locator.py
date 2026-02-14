import os
import winreg
import subprocess
from pathlib import Path
from langchain_core.tools import tool
from utils.logger import logger

@tool
def get_wechat_storage_path() -> str:
    """
    [定位] 深度探测 Windows 环境下当前登录微信的 FileStorage 物理路径。
    支持自定义路径探测，解决 AI 找不到语音、文件存档的问题。
    """
    try:
        # 1. 尝试从注册表获取微信自定义存储路径
        reg_path = r"Software\Tencent\WeChat"
        storage_path = ""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                # FileSavePath 是用户在微信设置中自定义的存储位置
                storage_path, _ = winreg.QueryValueEx(key, "FileSavePath")
        except Exception as reg_err:
            logger.warning(f"注册表探测失败: {reg_err}")

        # 2. 处理特殊路径标记 (微信默认使用 MyDocuments: 占位符)
        if "MyDocuments:" in storage_path:
            # 获取系统标准文档路径 (使用 PowerShell 保证准确性)
            try:
                # 显式使用 UTF-8 编码读取 PowerShell 输出
                cmd = 'powershell -NoProfile -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; [Environment]::GetFolderPath(\'MyDocuments\')"'
                documents_path = subprocess.check_output(
                    cmd, shell=True, encoding='utf-8'
                ).strip()
                storage_path = storage_path.replace("MyDocuments:", documents_path)
            except Exception as ps_err:
                logger.error(f"PowerShell 获取文档路径失败: {ps_err}")
                storage_path = os.path.join(os.environ["USERPROFILE"], "Documents")

        # 3. 如果注册表为空或无效，尝试默认路径
        if not storage_path or storage_path.strip() == "":
            storage_path = os.path.join(os.environ["USERPROFILE"], "Documents", "WeChat Files")

        # 4. 定位到具体的 FileStorage 目录
        base_dir = Path(storage_path)
        if not base_dir.exists():
            # 兼容性：尝试用户直接指定的路径名 (假设直接在基础路径下)
            return f"❌ 探测失败：找不到目录 {storage_path}"

        # 扫描用户文件夹 (通常是微信ID命名的目录, 至少包含 'Applet', 'FileStorage' 等)
        # 排除公用账户和模板文件夹
        candidates = [d for d in base_dir.iterdir() if d.is_dir() and (d / "FileStorage").exists()]
        
        if not candidates:
            # 再次深度尝试：寻找任何包含 FileStorage 的子目录
            return f"❌ 探测失败：在 {storage_path} 下未发现有效的微信数据目录。"

        # 选中最新修改的目录（代表当前活跃用户）
        active_user_dir = max(candidates, key=lambda d: d.stat().st_mtime)
        target_path = active_user_dir / "FileStorage" / "MsgAttach"
        
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"🧬 [Locator] 精准锁定微信存储: {target_path}")
        return str(target_path.absolute())

    except Exception as e:
        logger.error(f"❌ 路径探测异常: {str(e)}")
        return f"❌ 路径探测异常: {str(e)}"
