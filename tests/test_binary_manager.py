import unittest
from pathlib import Path

class TestBinaryManager(unittest.TestCase):
    """二进制组件管理器测试"""
    
    def test_binary_component_exists(self):
        """测试silk_v3_decoder.exe是否存在"""
        bin_dir = Path("tools/bin")
        silk_decoder = bin_dir / "silk_v3_decoder.exe"
        
        self.assertTrue(silk_decoder.exists(), "silk_v3_decoder.exe 应该存在于 tools/bin/ 目录中")
        self.assertGreater(silk_decoder.stat().st_size, 100000, "文件大小应该大于100KB")
    
    def test_binary_manager_import(self):
        """测试二进制管理器可以正常导入"""
        try:
            from tools.binary_manager import BinaryComponentManager, check_binary_components, initialize_binary_environment
            manager = BinaryComponentManager()
            self.assertIsNotNone(manager)
            self.assertIsNotNone(check_binary_components)
            self.assertIsNotNone(initialize_binary_environment)
        except ImportError as e:
            self.fail(f"导入失败: {e}")
    
    def test_binary_verification(self):
        """测试二进制组件验证功能"""
        from tools.binary_manager import BinaryComponentManager
        manager = BinaryComponentManager()
        
        # 验证组件
        results = manager.verify_components()
        
        # silk_v3_decoder.exe 应该存在
        self.assertIn("silk_v3_decoder.exe", results)
        self.assertTrue(results["silk_v3_decoder.exe"], "silk_v3_decoder.exe 应该验证通过")

if __name__ == '__main__':
    unittest.main()