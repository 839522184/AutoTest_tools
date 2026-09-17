# -*- coding: utf-8 -*-
import os

file_names = os.listdir("./")
print(file_names)
for index, name in enumerate(file_names):
    number_file = index + 1
    os.rename(name, str(number_file))
