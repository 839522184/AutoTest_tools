import os
import sys
import subprocess

test_path = "D:\\Auto_test"

# 当前路径
run_path = os.path.abspath(os.path.dirname(__file__))
print(run_path)

# 判断路径、文件存在
print(os.path.exists(run_path))  # True False

# 删除目录和路径下的文件并等待删除完成
p = subprocess.Popen("rmdir /s /q path", stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
p.wait()
