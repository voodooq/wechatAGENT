import pdfplumber
import re
import os
from langchain_core.tools import tool
from utils.logger import logger
from core.config import conf

@tool
def read_pdf_invoice(file_path: str) -> str:
    """
    [v10.1 Mutation] 专门读取 PDF 发票内容并提取核心信息。
    支持提取：发票号码、金额。
    
    Args:
        file_path: PDF 文件的路径。
    """
    if not os.path.exists(file_path):
        return f"❌ 错误：找不到文件 {file_path}"
        
    try:
        logger.info(f"📄 [PDF Reader] 正在解析发票: {file_path}")
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        # 简单正则搜索 (示例：匹配发票号码和金额)
        # 实际生产中建议根据不同发票格式优化正则
        invoice_no = re.search(r"发票号码[:：]\s*(\d+)", text)
        amount = re.search(r"小写[:：]\s*[¥￥]?\s*(\d+\.\d{2})", text)
        
        invoice_no_str = invoice_no.group(1) if invoice_no else "未识别"
        amount_str = amount.group(1) if amount else "未识别"
        
        result = (
            f"--- 发票解析成功 ---\n"
            f"文件: {os.path.basename(file_path)}\n"
            f"发票号码: {invoice_no_str}\n"
            f"合计金额: {amount_str}\n"
            f"--------------------\n"
            f"提示：数据已就绪，您可以要求我存入数据库。"
        )
        return result
        
    except Exception as e:
        logger.error(f"PDF 解析失败: {e}")
        return f"❌ PDF 解析崩溃: {str(e)}"
