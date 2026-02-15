import os
import importlib
import inspect
from pathlib import Path
from langchain_core.tools import BaseTool, tool
from utils.logger import logger

class ToolManager:
    """
    [能力管理器] 负责动态扫描并加载所有可用工具 (Tools)。
    支持：自动生成能力清单、工具自诊。
    """
    
    @staticmethod
    def load_all_tools() -> list:
        """
        [进化] 动态扫描并加载所有可用工具。
        """
        all_tools = []
        
        # 1. 静态导入核心演化工具 (确保生存能力)
        from tools.evolution import evolve_code, sync_to_github, request_hot_reload, report_evolution_progress
        from core.tools.wechat_locator import ultra_wechat_locator
        all_tools.extend([evolve_code, sync_to_github, request_hot_reload, report_evolution_progress, ultra_wechat_locator])

        # 2. 动态扫描 tools/ 目录
        tools_dir = Path(__file__).resolve().parent.parent / "tools"
        core_tools_dir = Path(__file__).resolve().parent / "tools"
        
        scan_paths = [tools_dir, core_tools_dir]
        
        for s_path in scan_paths:
            if not s_path.exists(): continue
            
            # 确定包前缀
            if s_path.name == "tools" and s_path.parent.name == "core":
                pkg_prefix = "core.tools"
            else:
                pkg_prefix = "tools"
            
            for file in s_path.glob("*.py"):
                if file.name.startswith("__"): continue
                
                module_name = f"{pkg_prefix}.{file.stem}"
                try:
                    module = importlib.import_module(module_name)
                    # 查找所有被 @tool 装饰的函数或 BaseTool 子类
                    for name, obj in inspect.getmembers(module):
                        if (hasattr(obj, "is_tool") and obj.is_tool) or isinstance(obj, BaseTool):
                            if obj not in all_tools:
                                all_tools.append(obj)
                except Exception as e:
                    logger.error(f"加载工具模块 {module_name} 失败: {e}")

        return all_tools

    @staticmethod
    def get_capability_string(tools_list: list) -> str:
        """
        生成“我能做什么”的能力说明字符串 (基于文档字符串)。
        """
        capabilities = []
        unique_tools = {}
        
        for t in tools_list:
            name = getattr(t, "name", getattr(t, "__name__", str(t)))
            if name in unique_tools: continue
            
            desc = getattr(t, "description", getattr(t, "__doc__", "无详细描述")).strip()
            # 只取第一行作为简要描述
            short_desc = desc.split('\n')[0] if desc else "无详细描述"
            
            unique_tools[name] = short_desc
            capabilities.append(f"- **{name}**: {short_desc}")
        
        return "\n".join(capabilities)
