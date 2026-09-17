import re
import subprocess
import time


def find_path_to_key(nested_dict, target_key):
    def traverse(d, path):
        if isinstance(d, dict):
            for key, value in d.items():
                new_path = path + [key]
                if key == target_key:
                    return new_path
                result = traverse(value, new_path)
                if result:
                    return result
        elif isinstance(d, list):
            for index, item in enumerate(d):
                new_path = path + [index]
                result = traverse(item, new_path)
                if result:
                    return result
        return None

    return traverse(nested_dict, [])


# 示例多层嵌套字典
nested_dict = {
    "outer": {
        "middle": {
            "inner": {
                "unique_key": "unique_value"
            }
        },
        "list_part": [
            {"not_the_key": "not_the_value"},
            {"also_not": "also_not_value"}
        ]
    }
}

target_key = "unique_key"
start_time = time.time()
path = find_path_to_key(nested_dict, target_key)
end_time = time.time()
print(end_time - start_time)
print(path)
