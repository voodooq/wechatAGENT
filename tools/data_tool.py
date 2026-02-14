"""
IronSentinel - 数据文件处理工具
"""
import os
# import pandas as pd # 移至函数内部实现惰性加载
from langchain_core.tools import tool
from core.config import conf
from utils.logger import logger

@tool
def read_and_analyze_file(file_path: str, query: str = "") -> str:
    """
    读取并分析本地数据文件 (Excel/CSV/JSON)。
    
    当用户询问关于某个文件的数据时，使用此工具。
    它会自动识别文件类型，读取内容，并返回摘要或前几行数据。
    
    Args:
        file_path: 文件绝对路径或相对路径 (相对于项目根目录)
        query: (可选) 关于数据的具体问题，用于辅助过滤或定位
    """
    try:
        # 1. 尝试导入 pandas
        try:
            import pandas as pd
        except ImportError:
            from tools.tools_common import format_error_payload
            return format_error_payload(
                "read_and_analyze_file",
                "缺少 pandas 核心数据分析库",
                "请立即调用 install_python_library('pandas') 修复环境后重试"
            )

        # 处理相对路径
        if not os.path.isabs(file_path):
            file_path = str(PROJECT_ROOT / file_path)
            
        if not os.path.exists(file_path):
            return f"❌ 文件不存在: {file_path}"
            
        ext = os.path.splitext(file_path)[1].lower()
        
        logger.info(f"正在读取数据文件: {file_path}")
        
        df = None
        if ext in ['.xlsx', '.xls']:
            try:
                # 显式导入 openpyxl
                import openpyxl
                df = pd.read_excel(file_path)
            except ImportError:
                from tools.tools_common import format_error_payload
                return format_error_payload(
                    "read_and_analyze_file",
                    "缺少 openpyxl (Excel 解析引擎)",
                    "请立即调用 install_python_library('openpyxl') 修复环境后重试"
                )
        elif ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext == '.json':
            df = pd.read_json(file_path)
        else:
            return f"❌ 不支持的文件类型: {ext} (仅支持 .xlsx, .xls, .csv, .json)"
            
        # 生成摘要
        rows, cols = df.shape
        columns = ", ".join(df.columns.tolist())
        head_data = df.head(5).to_markdown(index=False)
        
        summary = (
            f"✅ 文件读取成功: {os.path.basename(file_path)}\n"
            f"📊 维度: {rows} 行 x {cols} 列\n"
            f"📋 列名: {columns}\n\n"
            f"👀 前 5 行预览:\n{head_data}"
        )
        
        if len(df) > 5:
            summary += f"\n\n(剩余 {len(df) - 5} 行数据未显示)"
            
        return summary
        
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        from tools.tools_common import format_error_payload
        return format_error_payload(
            "read_and_analyze_file",
            str(e),
            "核实文件路径是否正确、文件是否被其他程序占用、或尝试列出目录确认文件名"
        )
