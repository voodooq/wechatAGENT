#!/usr/bin/env python3
"""
测试运行脚本

运行项目的所有单元测试。
"""
import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 如果有失败的测试，退出码为1
    sys.exit(0 if result.wasSuccessful() else 1)