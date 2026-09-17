# !/usr/bin/python
# -*-coding:utf-8 -*-


import subprocess
import os

"""
音频流解决语音测试的思路
核心：
    注入音频流："adb shell mic_in < {audio_file_path}"
    捕获输出音频流：
        方案一：视频录制后解析视频的音频
        方案二：使用 sndcpy 工具
"""


class Audios():
    def __init__(self):
        pass

    def mic_in(self, name):
        """
        注入音频流到终端
        :param name: 音频文件名 .wav
        :return:
        """
        audio_file_path = os.path.join("", name)
        try:
            # 构建 adb 命令
            adb_command = f"adb shell mic_in < {audio_file_path}"
            print("adb_command: {}".format(adb_command))
            # 执行 adb 命令
            process = subprocess.Popen(adb_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # 获取命令执行结果
            stdout, stderr = process.communicate()
            # 检查返回码
            if process.returncode == 0:
                print("音频流发送成功")
            else:
                print(f"音频流发送失败，错误信息: {stderr.decode('utf-8')}")
        except Exception as e:
            print(f"发生错误: {e}")


if __name__ == '__main__':
    audios = Audios()
