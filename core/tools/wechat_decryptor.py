import os
from pathlib import Path
from langchain_core.tools import tool
from utils.logger import logger

@tool
def decrypt_wechat_dat(file_path: str) -> str:
    """
    [解密] 自动探测 XOR 密钥并还原微信 .dat 加密文件 (v11.0)。
    支持：JPG, PNG, GIF 的精准探测与验证。
    """
    input_path = Path(file_path)
    if not input_path.exists():
        return f"❌ 错误：找不到文件 {file_path}"

    try:
        with open(input_path, 'rb') as f:
            data = f.read()

        if len(data) < 2:
            return "❌ 错误：文件太小，无法探测密钥。"

        # 1. 自动探测 XOR 密钥 (常用文件头：JPG(0xFFD8), PNG(0x8950), GIF(0x4749))
        possible_headers = [0xFF, 0x89, 0x47]
        xor_key = None
        ext = ".decoded"
        
        for head in possible_headers:
            key = data[0] ^ head
            # 验证第二个字节是否匹配
            if head == 0xFF and (data[1] ^ key) == 0xD8: xor_key = key; ext = ".jpg"; break
            if head == 0x89 and (data[1] ^ key) == 0x50: xor_key = key; ext = ".png"; break
            if head == 0x47 and (data[1] ^ key) == 0x49: xor_key = key; ext = ".gif"; break

        if xor_key is None:
            return "❌ 失败：未能探测到有效的 XOR 密钥，文件可能未加密或格式不支持。"

        # 2. 执行全文件异或解码
        decrypted_data = bytearray(b ^ xor_key for b in data)
        
        # 3. 保存至临时目录
        from core.config import conf
        output_dir = conf.project_root / "temp" / "decrypted"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{input_path.stem}_decrypted{ext}"
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)

        logger.info(f"🧬 [Decryptor] v11.0 成功解密文件: {output_path} (Key: {hex(xor_key)})")
        return str(output_path.absolute())

    except Exception as e:
        logger.error(f"❌ 解密异常: {e}")
        return f"❌ 解密异常: {str(e)}"
