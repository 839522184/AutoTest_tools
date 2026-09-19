import uuid


def generate_unique_id():
    """
    使用UUID生成唯一标识符
    返回一个32字符的十六进制字符串
    """
    return uuid.uuid4().hex


# 示例使用
print(generate_unique_id())  # 输出类似: 'f47ac10b58cc4372a5670e02b2c3d479'
