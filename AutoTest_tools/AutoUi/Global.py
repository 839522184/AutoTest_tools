# !/usr/bin/python
# -*-coding:utf-8 -*-
"""
全局参数配置，不允许出现逻辑处理
"""
import os
import sys

if getattr(sys, "frozen", False):
    # 打包特殊路径配置
    main_run_path = os.path.dirname(sys.executable)
    allure_path = os.path.join(main_run_path, "allure_dir")
    base_excel_path = main_run_path + "\\"
    # 临时存放目录
    temporary_path = os.path.join(main_run_path, "temp")
    # Crash截图存放文件夹
    crash_path = os.path.join(main_run_path, "CrashPic")
    package_flag = True
else:
    # 非打包路径配置
    main_run_path = os.path.dirname(__file__)
    allure_path = os.path.join(main_run_path, "allure_dir")
    base_excel_path = "\\".join(main_run_path.split("\\")) + "\\"
    # 临时存放目录
    temporary_path = os.path.join(main_run_path, "temp")
    # Crash截图存放文件夹
    crash_path = os.path.join(main_run_path, "CrashPic")
    package_flag = False

# ======================================================================================================
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* v Path 区间 v *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
'''此区域只允许路径到文件夹，如需具体到文件名请于代码内自行组装'''
base_path = os.path.dirname(os.path.abspath(__file__))
# 例如：项目根目录: 'D:\\My_Project\\zui_test\\zui_test'
testcase_path = main_run_path

# case路径 无论是否打包路径都是此路径
cases_path = os.path.dirname(os.path.abspath(__file__))

# 三方资源目录
third_path = testcase_path + "\\ThirdFunction"

# 三方文件目录
third_files_path = base_path + "\\ThirdFunction\\ThirdFiles"

# 设备sdcard根目录
sdcard_path = '/sdcard/'

# jar包路径
jar_path = base_path + "\\ThirdFunction\\ThirdFiles\\zui-2.0.0-fat-tests.jar"

# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* ^ Path 区间 ^ *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
# ======================================================================================================
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-* v 全局变量命名 区间 v *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
