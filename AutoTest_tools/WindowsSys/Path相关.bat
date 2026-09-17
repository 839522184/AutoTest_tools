:: 当前bat文件路径
set now_path=%~dp0

:: 获取运行的环境目录，两种方式
set run_path=%cd%
set run_path=!cd!

:: 配置临时环境变量
set Path="xxxx"

:: 配置环境变量到用户变量
setx "变量名" "变量值"

:: 配置环境变量到系统变量
setx "变量名" "变量值" /m

:: 配置环境变量到Path变量
setx "Path" "%Path%";"your_path" /m

:: 配置注册表（新建一项Test01数据，类型是REG_DWORD 数据数值为1，/f可取消提醒）
reg add HKEY_CURRENT_USER\path1\path2 /v Test01 /t REG_DWORD /d 1 /f