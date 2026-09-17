:: 打开启动项管理器
win R -> taskschd.msc

:: 配置计划 - 电脑启动时执行python脚本
schtasks /create /sc onstart /tn "MyPythonTask" /tr "D:\My_Project\Test\Test_Env\Scripts\python.exe D:\My_Project\Test\DebugTest\Windows_Debug\get_startup_time_new.py"
:: 参数说明
:: /sc onstart 启动时执行
:: /tn "MyPythonTask" 计划名称
:: /tr 接pathon解释器路径 空格 执行脚本路径

:: 获取python解释器方式
py_path = sys.executable
:: 获取当前执行文件绝对路径
file_path = path = os.path.abspath(__file__)

:: 删除计划任务
schtasks /delete /tn MyPythonTask /f
:: 参数说明
:: tn 任务名
:: /f 强制操作，无需确认