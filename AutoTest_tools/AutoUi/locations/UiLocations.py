# !/usr/bin/python
# -*-coding:utf-8 -*-


from .mi14 import mi14

android_name = "mi14"
if android_name == "mi14":
    location_tree = mi14


class SettingsDoActions():
    def __init__(self, devices):
        self.device = devices
