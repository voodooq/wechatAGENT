import sys
import subprocess
import importlib
from langchain_core.tools import tool
from utils.logger import logger

# [v7.1 Safety Configuration]
# 兼容性锁定表：防止 AI 安装不稳定的最新版库 (如 numpy 2.0 引起的破坏性变更)
COMPATIBILITY_MAP = {
    "numpy": "numpy<2.0.0",
    "pandas": "pandas>=2.0.0",
    "Pillow": "Pillow>=10.0.0"
}

# 软件黑名单关键词：防止安装游戏、社交媒体或超大型无用软件
PROHIBITED_KEYWORDS = [
    "game", "steam", "wechat", "tiktok", "douyin", "epic", "battle.net", 
    "genshin", "honkai", "warframe", "call of duty", "league of legends"
]

@tool
def install_python_library(library_name: str) -> str:
    """
    [自我进化-核心] 当任务因缺少 Python 库 (ModuleNotFoundError) 失败时调用。
    它会自动安装库并热加载，无需重启程序。
    参数: library_name (例如 'pandas', 'openpyxl', 'python-pptx')
    """
    logger.info(f"🛠️ [System Evolution v7.1] 正在处理 Python 库演化: {library_name}...")
    try:
        # 1. 检查是否有兼容性锁定版本
        pkg_to_install = COMPATIBILITY_MAP.get(library_name, library_name)
        if pkg_to_install != library_name:
            logger.info(f"应用兼容性锁定建议: {library_name} -> {pkg_to_install}")

        # 使用当前 Python 解释器执行 pip install
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_to_install, "--no-input"])
        
        # 关键：刷新系统模块缓存，让 Python 知道新库来了
        importlib.invalidate_caches()
        
        return f"✅ 库 '{library_name}' 已成功热安装。请立即重新执行刚才失败的任务。"
    except Exception as e:
        logger.error(f"进化失败：无法安装库 '{library_name}'。原因: {e}")
        return f"【系统反馈】❌ pip 安装失败: {str(e)}。无法自动修复。"

@tool
def install_windows_software(software_name: str) -> str:
    """
    [自我进化-核心] 当任务因缺少外部软件 (如 'VLC', 'Notepad++') 失败时调用。
    它会通过微软 Winget 包管理器下载并静默安装。
    参数: software_name (软件名称或 ID)
    """
    logger.info(f"🛠️ [System Evolution v7.1] 正在处理软件安全性预检: {software_name}...")
    try:
        # 0. 安全过滤：禁止安装黑名单关键词软件
        lower_name = software_name.lower()
        for keyword in PROHIBITED_KEYWORDS:
            if keyword in lower_name:
                logger.warning(f"安全拦截：检测到禁装关键词 '{keyword}'，已拒绝安装请求。")
                return f"❌ 安全策略拒绝：软件 '{software_name}' 被识别为娱乐或非办公软件，已过滤。"

        # 1. 先搜索软件，确保软件存在于 winget 源
        search_cmd = f"winget search \"{software_name}\" --source winget --accept-source-agreements"
        search_res = subprocess.run(search_cmd, capture_output=True, text=True, shell=True)
        
        if "No package found" in search_res.stdout:
            return f"❌ 未在微软商店 (winget) 找到软件或包: {software_name}。请确认名称是否准确。"

        # 2. 静默安装
        # --silent: 静默安装，不弹窗
        # --accept-package-agreements: 自动同意 EULA 协议
        install_cmd = f"winget install --name \"{software_name}\" --silent --accept-source-agreements --accept-package-agreements --source winget"
        
        logger.info(f"执行安装指令: {install_cmd}")
        process = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode == 0:
            return f"✅ 软件 '{software_name}' 已静默安装完成！您现在可以尝试启动它了。"
        else:
            error_msg = process.stderr or process.stdout
            return f"【系统反馈】❌ 安装失败。请确保您是【以管理员身份运行】。详细报错: {error_msg[:150]}"

    except Exception as e:
        logger.error(f"系统进化逻辑崩溃: {e}")
        return f"【系统反馈】❌ 软件进化逻辑异常: {str(e)}"
