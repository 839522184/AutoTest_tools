# -*- coding: utf-8 -*-
import os
import time
import sys

if getattr(sys, "frozen", False):
    # 打包特殊路径配置
    main_run_path = os.path.dirname(sys.executable)
else:
    # 非打包路径配置
    main_run_path = os.path.dirname(__file__)
print(main_run_path)

file_names = os.listdir(main_run_path)
for name in file_names:
    file_type = name.rsplit(".")[-1]
    file_name = name.split(".")[0]
    if file_name.isdigit() and len(file_name) == 17:
        continue
    if ".py" in name or ".exe" in name:
        continue
    time_str = str(time.time()).replace(".", "").ljust(17, "0")
    # 不足17位的补零  .ljust(17, "0")
    new_name = str(time_str) + "." + file_type
    os.rename(name, new_name)
    print(f"{name} --> {new_name}")
    time.sleep(0.001)
