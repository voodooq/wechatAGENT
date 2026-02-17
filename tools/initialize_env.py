import os
import sys
import shutil
from pathlib import Path

def ensure_binary_components():
    """确保所有必需的二进制组件都存在"""
    bin_dir = Path("tools/bin")
    bin_dir.mkdir(exist_ok=True)
    
    # 必需的二进制文件列表
    required_binaries = {
        "silk_v3_decoder.exe": "微信语音解码核心组件"
    }
    
    for binary_name, description in required_binaries.items():
        binary_path = bin_dir / binary_name
        
        if not binary_path.exists():
            print(f"⚠️  {description} 缺失: {binary_name}")
            print(f"   请从项目仓库下载或手动放置到 {bin_dir} 目录")
            return False
        else:
            print(f"✅ {description} 已就绪: {binary_name}")
    
    return True

def main():
    """初始化环境"""
    print("🔧 初始化运行环境...")
    
    # 确保二进制组件
    if not ensure_binary_components():
        print("❌ 环境初始化失败：缺少必需的二进制组件")
        sys.exit(1)
    
    print("✅ 环境初始化完成！")

if __name__ == "__main__":
    main()