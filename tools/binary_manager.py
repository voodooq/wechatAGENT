import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List
from langchain_core.tools import tool
from utils.logger import logger

class BinaryComponentManager:
    """二进制组件管理器"""
    
    def __init__(self):
        self.bin_dir = Path("tools/bin")
        self.bin_dir.mkdir(exist_ok=True)
        
        # 定义必需的二进制组件
        self.required_components = {
            "silk_v3_decoder.exe": {
                "description": "微信语音解码核心组件",
                "size": 179037,  # 预期文件大小
                "source": "git_repository"  # 来源：Git仓库
            }
        }
    
    def verify_components(self) -> Dict[str, bool]:
        """验证所有必需组件是否存在且完整"""
        verification_results = {}
        
        for component_name, component_info in self.required_components.items():
            component_path = self.bin_dir / component_name
            
            if not component_path.exists():
                verification_results[component_name] = False
                logger.warning(f"❌ 组件缺失: {component_name} - {component_info['description']}")
            else:
                # 检查文件大小（简单完整性验证）
                actual_size = component_path.stat().st_size
                expected_size = component_info['size']
                
                if abs(actual_size - expected_size) <= 1000:  # 允许1KB的差异
                    verification_results[component_name] = True
                    logger.info(f"✅ 组件验证通过: {component_name}")
                else:
                    verification_results[component_name] = False
                    logger.warning(f"⚠️  组件大小异常: {component_name} (实际: {actual_size}, 预期: {expected_size})")
        
        return verification_results
    
    def get_missing_components(self) -> List[str]:
        """获取缺失的组件列表"""
        verification_results = self.verify_components()
        return [name for name, exists in verification_results.items() if not exists]
    
    def ensure_all_components(self) -> bool:
        """确保所有组件都存在"""
        missing_components = self.get_missing_components()
        
        if not missing_components:
            logger.info("✅ 所有二进制组件都已就绪")
            return True
        
        logger.error(f"❌ 缺失以下组件: {', '.join(missing_components)}")
        logger.info("💡 请确保从 Git 仓库完整克隆项目，或手动下载缺失的组件")
        return False

# 全局实例
binary_manager = BinaryComponentManager()

@tool
def check_binary_components() -> str:
    """检查二进制组件状态"""
    try:
        verification_results = binary_manager.verify_components()
        missing = binary_manager.get_missing_components()
        
        result = "🔧 二进制组件状态检查\n" + "=" * 30 + "\n"
        
        for component, exists in verification_results.items():
            status = "✅" if exists else "❌"
            description = binary_manager.required_components[component]['description']
            result += f"{status} {component}: {description}\n"
        
        if missing:
            result += f"\n⚠️  缺失组件: {', '.join(missing)}\n"
            result += "💡 解决方案: 重新克隆仓库或手动下载缺失文件到 tools/bin/ 目录"
        else:
            result += "\n✅ 所有组件都已就绪！"
        
        return result
        
    except Exception as e:
        logger.error(f"检查二进制组件失败: {e}")
        return f"❌ 检查失败: {str(e)}"

@tool  
def initialize_binary_environment() -> str:
    """初始化二进制环境"""
    try:
        success = binary_manager.ensure_all_components()
        if success:
            return "✅ 二进制环境初始化成功！"
        else:
            return "❌ 二进制环境初始化失败，请检查缺失的组件"
    except Exception as e:
        logger.error(f"初始化二进制环境失败: {e}")
        return f"❌ 初始化失败: {str(e)}"