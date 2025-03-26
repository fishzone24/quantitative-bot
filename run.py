#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CryptoQuantTrader 启动脚本
"""

import os
import sys

# 确保能够引用项目中的模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # 默认启动菜单界面
    from menu import run_menu
    run_menu()
except Exception as e:
    print(f"启动菜单失败: {str(e)}")
    print("尝试以命令行模式运行...")
    
    try:
        from main import main
        main()
    except Exception as e:
        print(f"启动失败: {str(e)}")
        print("请确保已安装所有依赖包，命令: pip install -r requirements.txt")
        sys.exit(1) 