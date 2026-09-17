# !/usr/bin/python
# -*-coding:utf-8 -*-

"""
pytest参数说明
    -vs: 开启详细输出模式，比如每个测试用例的名称、执行结果（通过、失败、跳过等）
    -p: 用于指定要加载或禁用的 pytest 插件
        no:faulthandler：表示禁用 faulthandler 插件。faulthandler 插件会在 Python 进程崩溃时输出详细的堆栈跟踪信息，禁用该插件可以避免在某些情况下不必要的信息输出。
    -m: 用于根据测试用例的标记（mark）来筛选要执行的测试用例
"""
import datetime
import pytest
import os
from Global import *


def set_allure_path(src_path):
    """
    :param src_path:
    :return:
    """
    # 获取当前时间
    now = datetime.datetime.now()
    # 以指定格式输出时间
    formatted_time = now.strftime("%Y%m%d%H%M%S")
    return os.path.join(src_path, formatted_time)


if __name__ == '__main__':
    # 定制allure报告路径
    allure_path = set_allure_path(src_path=allure_path)

    # case路径
    case_path = os.path.join(main_run_path, "test_case", "test_1.py") + "::Test01"

    # pytest.main(
    #     ["-vs", "-p", "no:faulthandler", "-m", "new", case_path],
    # )

    pytest.main(
        ["-vs", "-p", "no:faulthandler", f"--alluredir={allure_path}", case_path],
    )
