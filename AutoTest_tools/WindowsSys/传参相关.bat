:: 不同文件传参
:: - A.bat -
echo call B.bat
call B.bat 1234 5678

:: - B.bat - ，接收参数 %0表示自己 %1 接收第一个参数，依次递加到 %9
set arges1=%1
set arges2=%2
echo %arges1%
echo %arges2%
:: 打印出arges1等于 1234，arges2等于5678

:: 接收外部参数 CMD
B.bat C:windows32 234
:: 打印出arges1等于 C:windows32，arges2等于234
:: 需注意若参数有空格要使用双引号包起来