# 导出pip list
# pip freeze > requirements.txt

# 从 requirements.txt 安装
# pip install -r requirements.txt

# 安装指定版本的包，降级包
# pip install pkg_name==version
# pip install request==1.0.1

# 查询包的所有版本号（老版本使用pip search pkg_name查询，但在后续pip版本中被废弃了）
# pip install pkg_name==*
# pip install requests==*

# 更新包，升级包
# pip install --upgred requests

# 配置从国内镜像源地址安装
# pip install pkg_name -i https://pypi.tuna.tsinghua.edu.cn/simple

# 查看包依赖列表
# pip show --files pkg_name
# pip show --files requests