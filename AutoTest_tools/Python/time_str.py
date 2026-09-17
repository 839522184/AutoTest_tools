import datetime
import time

# 当前时间戳
print(time.time())

# 当前时间 Y/M/D
# 获取当前时间
now = datetime.datetime.now()
# 以指定格式输出时间
formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")  # 2025-04-30 16:16:32
print(formatted_time)
# 以指定格式输出时间
formatted_time = now.strftime("%H:%M:%S")  # 16:16:32
print(formatted_time)