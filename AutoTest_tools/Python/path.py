import os
import sys

# 获取当前文件所在路径
# d:\My_Project\knowledge-base\Python\path.py
current_file_path = os.path.abspath(__file__)

# 获取当前文件夹
# d:\My_Project\knowledge-base\Python
current_directory =  os.path.dirname(os.path.abspath(__file__))

# python 打包exe后的路径问题
if getattr(sys, "frozen", False):
    # 打包特殊路径配置
    main_run_path = os.path.dirname(sys.executable)
else:
    # 非打包路径配置
    main_run_path = os.path.dirname(__file__)
    
# 获取正在执行的文件
os.path.basename(__file__)

