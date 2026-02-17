#!/usr/bin/env python3
"""
测试运行脚本

运行项目的所有单元测试和功能测试。
"""
import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试模块
    test_modules = [
        'tests.test_deduplicator',
        'tests.test_auto_voice_processor', 
        'tests.test_wechat_account_manager',
        'tests.test_one_click_voice',
        'tests.test_binary_manager'
    ]
    
    for module in test_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
        except ImportError as e:
            print(f"警告: 无法导入测试模块 {module}: {e}")
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)