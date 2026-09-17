import os
from pydub import AudioSegment
import time
import subprocess


def m4a_to_mp3():
    file_path = ""  # m4a文件路径
    new_path = ""  # 转换后的保存路径
    names = os.listdir(file_path)
    print(names)
    for name in names:
        new_name = name.replace("m4a", "mp3")
        print(os.path.join(file_path, name), os.path.join(new_path, new_name))

        # 加载M4A文件
        print(f"加载 {os.path.join(file_path, name)}")
        m4a_path = os.path.join(file_path, name)
        audio = AudioSegment.from_file(m4a_path, format="m4a")

        # 导出为MP3（设置比特率为320kbps，可根据需要调整）
        print(f"转mp3 {os.path.join(new_path, new_name)}")
        mp3_path = os.path.join(new_path, new_name)
        audio.export(mp3_path, format="mp3", bitrate="320k")

def repair_m4a(input_path, output_path=None, ffmpeg_path="ffmpeg"):
    """
    修复M4A文件，确保输出路径为具体文件而非目录

    :param input_path: 输入M4A文件路径
    :param output_path: 输出修复后的文件路径（默认自动生成）
    :param ffmpeg_path: FFmpeg可执行文件路径
    :return: 修复成功返回True，失败返回False
    """
    ffmpeg_path = r"D:\ffmpeg\bin\ffmpeg.exe"  # 解压ffmpeg-7.1.1-essentials_build.zip并加bin路径到环境变量
    # 1. 验证输入文件
    if not os.path.exists(input_path):
        print(f"错误：输入文件不存在 - {input_path}")
        return False

    if not input_path.lower().endswith(".m4a"):
        print(f"错误：输入文件不是M4A格式 - {input_path}")
        return False

    # 2. 处理输出路径（确保是文件而非目录）
    if not output_path:
        # 自动生成输出文件名（在原文件名后加_repaired）
        dir_name = os.path.dirname(input_path)
        file_name = os.path.basename(input_path)
        name, ext = os.path.splitext(file_name)
        output_path = os.path.join(dir_name, f"{name}_repaired{ext}")
    else:
        # 检查输出路径是否为目录，若是则自动生成文件名
        if os.path.isdir(output_path):
            file_name = os.path.basename(input_path)
            output_path = os.path.join(output_path, file_name)

    # 3. 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"已创建输出目录：{output_dir}")

    # 4. 检查FFmpeg是否可用
    try:
        subprocess.run(
            [ffmpeg_path, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
    except FileNotFoundError:
        print(f"错误：未找到FFmpeg，请检查路径 - {ffmpeg_path}")
        return False
    except Exception as e:
        print(f"FFmpeg检查失败：{str(e)}")
        return False

    # 5. 执行修复命令（快速修复：复制流）
    command = [
        ffmpeg_path,
        "-v", "error",  # 只输出错误信息
        "-i", input_path,  # 输入文件
        "-c:a", "copy",  # 直接复制音频流（不重新编码）
        "-y",  # 覆盖现有文件
        output_path  # 输出文件（必须是具体文件名）
    ]

    try:
        # 执行命令并捕获输出
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 检查执行结果
        if result.returncode != 0:
            print(f"快速修复失败，错误信息：{result.stderr}")
            # 尝试强制重新编码修复
            return force_reencode(input_path, output_path, ffmpeg_path)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"修复成功，文件保存至：{output_path}")
            return True
        else:
            print("修复失败：未生成输出文件")
            return False

    except Exception as e:
        print(f"执行修复时出错：{str(e)}")
        return False


def force_reencode(input_path, output_path, ffmpeg_path):
    """当快速修复失败时，尝试重新编码"""
    print("尝试重新编码修复...")
    command = [
        ffmpeg_path,
        "-v", "error",
        "-i", input_path,
        "-c:a", "aac",  # 重新编码为AAC格式
        "-b:a", "192k",  # 比特率
        "-y",
        output_path
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode == 0 and os.path.getsize(output_path) > 0:
            print(f"重新编码修复成功：{output_path}")
            return True
        else:
            print(f"重新编码失败，错误信息：{result.stderr}")
            return False
    except Exception as e:
        print(f"重新编码时出错：{str(e)}")
        return False

def file_rename():
    file_path = ""  # 需要重命名的路径
    # new_path = r"D:\My_Project\Py_Word\knowledge-base\AutoUi\temp\唤醒语料\AI"
    names = os.listdir(file_path)
    print(names)
    for name in names:
        new_name = name.replace("-(", "-").replace(")", "").replace(" (", "-")  # 修改此规则，new_name为修改后的名字
        print(os.path.join(file_path, name), os.path.join(file_path, new_name))
        os.rename(os.path.join(file_path, name), os.path.join(file_path, new_name))