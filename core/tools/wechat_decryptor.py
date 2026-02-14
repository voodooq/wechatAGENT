import os
from pathlib import Path
from langchain_core.tools import tool
from utils.logger import logger

@tool
def decrypt_wechat_dat(file_path: str) -> str:
    """
    [解密] 自动识别并破解微信 PC 端 .dat 加密文件。
    支持：将加密的 .dat 媒体流还原为原始格式。
    """
    input_path = Path(file_path)
    if not input_path.exists():
        return f"❌ 错误：找不到文件 {file_path}"

    try:
        with open(input_path, 'rb') as f:
            data = f.read()

        if not data:
            return "❌ 错误：文件为空。"

        # 1. 自动探测 XOR 密钥 (通过常用图片头进行暴力匹配)
        # JPG: 0xFF D8 | PNG: 0x89 50 | GIF: 0x47 49
        headers = [0xFF, 0xD8, 0x89, 0x50, 0x47, 0x49]
        xor_key = None
        
        # 尝试通过第一个字节推算密钥，并验证第二个字节
        for header_byte in headers:
            potential_key = data[0] ^ header_byte
            # 验证第二个字节是否也符合头部特征
            if len(data) > 1 and (data[1] ^ potential_key) in headers:
                xor_key = potential_key
                break
        
        if xor_key is None:
            # 针对非图片媒体的兜底：尝试 0x00 填充位推算（部分版本适用）
            # 或者返回原始数据（可能未加密）
            return "❌ 失败：未能探测到有效的 XOR 密钥，文件可能未加密或格式不支持。"

        # 2. 执行全文件异或解码
        decrypted_data = bytearray(b ^ xor_key for b in data)
        
        # 3. 保存至临时目录
        from core.config import conf
        output_dir = conf.PROJECT_ROOT / "temp" / "decrypted"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 根据推导出的头部猜测后缀
        ext = ".jpg"
        if (decrypted_data[0] == 0x89): ext = ".png"
        elif (decrypted_data[0] == 0x47): ext = ".gif"
        
        output_path = output_dir / f"{input_path.stem}_decrypted{ext}"
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)

        logger.info(f"🧬 [Decryptor] 成功解密文件: {output_path} (Key: {hex(xor_key)})")
        return str(output_path.absolute())

    except Exception as e:
        logger.error(f"❌ 解密异常: {e}")
        return f"❌ 解密异常: {str(e)}"
