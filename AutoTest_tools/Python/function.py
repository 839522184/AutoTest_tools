import os
import sys
import argparse


def test01():
    """
    测试01
    return: 
    """


# 获取函数注释
print(test01.__doc__)

# 传参相关
parser = argparse.ArgumentParser(description='manual to this script')
parser.add_argument("-n", "--name", type=str, default="test1")
parser.add_argument("-v", "--version", type=int, default=1)
args = parser.parse_args()
print(args.name)
print(args.version)
