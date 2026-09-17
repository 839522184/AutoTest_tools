# 进制转换
a = 10

a_b = bin(a)
print("十进制转二进制数：{}".format(a_b))

a_o = oct(a)
print("十进制转八进制数：{}".format(a_o))

a_h = hex(a)
print("十进制转十六进制数：{}".format(a_h))

a = int(a_b, 2)
print("二进制转十进制数：{}".format(a))

a = int(a_o, 8)
print("八进制转十进制数：{}".format(a))

a = int(a_h, 16)
print("十六进制转十进制数：{}".format(a))


# 字典数据更新
my_dict = {"a": "xxxxx", "g": {"i": "xx", "j": "xxx"}}
my_dict.update({"a": "haha"})
print(my_dict)

