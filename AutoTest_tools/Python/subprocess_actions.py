import subprocess

# 执行命令，等待完成
subprocess.run(["ls", "-l"])

# 带 shell 执行（注意安全风险）
subprocess.run("ls -l", shell=True)

# run() 完整参数示例 --- 阻塞 ---
# result = subprocess.run(["ls", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, timeout=10, cwd="/path/to/dir")
result = subprocess.run(
    ["ls", "-l"],  # 命令列表
    stdout=subprocess.PIPE,  # 捕获标准输出
    stderr=subprocess.PIPE,  # 捕获标准错误
    text=True,  # 以文本形式返回
    check=True,  # 如果返回码非零则抛出异常
    timeout=10,  # 超时设置(秒)
    cwd="/path/to/dir"  # 设置工作目录
)
print(result.stdout)


# Popen() 完整参数示例 --- 非阻塞 ---
# 创建子进程执行外部命令
process = subprocess.Popen(
    # 要执行的命令及参数（列表形式）
    ["python", "script.py"],

    # 允许shell执行
    shell=True,

    # 标准输入配置：创建管道以便向子进程发送数据
    stdin=subprocess.PIPE,

    # 标准输出配置：创建管道以便获取子进程输出
    stdout=subprocess.PIPE,

    # 标准错误配置：创建管道以便获取子进程错误信息
    stderr=subprocess.PIPE,

    # 设置子进程的工作目录（current working directory）
    cwd="/project",

    # 设置子进程的环境变量（这里设置Python模块搜索路径）
    env={"PYTHONPATH": "/lib"},

    # 以文本模式处理输入输出（替代universal_newlines）
    text=True,

    # 指定文本编码为UTF-8
    encoding="utf-8",

    # 编码错误处理方式：忽略错误字符
    errors="ignore",

    # 在新会话中创建进程（使子进程独立于父进程）
    start_new_session=True
)

# 示例：实时获取Popen的输出
proc = subprocess.Popen(["tail", "-f", "logfile.txt"],
                       stdout=subprocess.PIPE,  # 配置标准输出参数
                       text=True  # 以文本形式处理输出
                        )
try:
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        print(line.strip())
except KeyboardInterrupt:
    proc.terminate()

# 示例：交互式输出
# 交互式输入
proc = subprocess.Popen(
    ["python"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

proc.stdin.write("print('Hello from subprocess')\n")  # 写命令操作
proc.stdin.flush()  # 发送操作
output = proc.stdout.read()
print(output)
proc.stdin.write("exit()\n")
proc.stdin.flush()

output = proc.stdout.read()
print(output)