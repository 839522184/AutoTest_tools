# !/usr/bin/python
# -*-coding:utf-8 -*-


import os
import cv2
import numpy as np
import time
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from collections import Counter
from PIL import Image
from rapidocr_onnxruntime import RapidOCR


# ***********************
# pip install opencv-python numpy scikit-learn matplotlib rapidocr-onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple
# ***********************


class CVFunction():

    def __init__(self):
        pass

    def find_image_position_pixel(self, template_path, target_path, threshold=0.8, gray_compare=True, display=False):
        """
        通过模板匹配查找图片2在图片1中的位置，像素点匹配
        参数:
            template_path: 主图路径 (大图)
            target_path: 模板路径 (小图)
            threshold: 匹配阈值 (0-1)
            gray_compare: 是否转为灰度图匹配
            display: 是否调试，调试模式会展示框选后的底图
        返回:
            result: 包含位置和相似度的字典列表
                    (可能多个匹配位置)
                    [{"x": int, "y": int, "width": int, "height": int, "similarity": float}, ...]
            若未找到返回空列表
        """
        # 匹配算法，像素点匹配
        method = cv2.TM_CCOEFF_NORMED

        # 读取图片
        img_main = cv2.imread(template_path)
        img_template = cv2.imread(target_path)

        if img_main is None or img_template is None:
            raise ValueError("无法读取图片，请检查文件路径")

        # 转换为灰度图（可选）
        if gray_compare:
            img_main = cv2.cvtColor(img_main, cv2.COLOR_BGR2GRAY)
            img_template = cv2.cvtColor(img_template, cv2.COLOR_BGR2GRAY)

        # 用于画框的彩色主图副本
        img_main_color = img_main.copy()

        # 检查模板尺寸是否大于主图
        h_main, w_main = img_main.shape[:2]
        h_tpl, w_tpl = img_template.shape[:2]
        if h_tpl > h_main or w_tpl > w_main:
            raise ValueError("模板图片尺寸不能大于主图")

        # 执行模板匹配
        result = cv2.matchTemplate(img_main, img_template, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 根据匹配方法确定最佳匹配位置
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            top_left = min_loc
            similarity = 1 - min_val if method == cv2.TM_SQDIFF_NORMED else None
        else:
            top_left = max_loc
            similarity = max_val

        # 筛选超过阈值的匹配区域
        locations = []
        similarities = []
        if similarity >= threshold:
            # 获取所有匹配位置
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                loc = np.where(result <= threshold)
            else:
                loc = np.where(result >= threshold)

            # 遍历所有匹配点
            for pt in zip(*loc[::-1]):
                x, y = pt
                locations.append({
                    "x": x,
                    "y": y,
                    "width": w_tpl,
                    "height": h_tpl,
                    "similarity": float(result[y, x])  # 实际匹配值
                })
                similarities.append(float(result[y, x]))

                if display:
                    # 画框操作
                    bottom_right = (x + w_tpl, y + h_tpl)
                    cv2.rectangle(img_main_color, (x, y), bottom_right, (0, 255, 0), 2)

                    # 创建一个可调整大小的窗口
                    cv2.namedWindow('Matching Result', cv2.WINDOW_NORMAL)

                    # 设置窗口的初始大小，这里设置为 800x600，你可以根据需要修改
                    cv2.resizeWindow('Matching Result', 800, 450)

                    # 显示匹配结果
                    cv2.imshow('Matching Result', img_main_color)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()

            if locations:
                # 获取匹配度最高的信息
                best_match_index = similarities.index(max(similarities))
                best_location = locations[best_match_index]
                print("获取到图像匹配信息：{}".format(best_location))
                return best_location
            # # 保存画框后的图像
            # output_path = "output_image.jpg"
            # cv2.imwrite(output_path, img_main_color)
            # print(f"画框后的图像已保存到 {output_path}")
        else:
            print("图像匹配失败")
            return None

    def find_image_position_feature(self, template_path, target_path, threshold=0.8, gray_compare=True, display=False):
        """
        通过特征点匹配查找图片2在图片1中的位置
        参数:
            template_path: 主图路径 (大图)
            target_path: 模板路径 (小图)
            threshold: 匹配阈值 (0-1)
            gray_compare: 是否转为灰度图匹配
            display: 是否调试，调试模式会展示框选后的底图
        返回:
            result: 包含位置和相似度的字典列表
                    (可能多个匹配位置)
                    [{"x": int, "y": int, "width": int, "height": int, "similarity": float}, ...]
            若未找到返回空列表
        """
        MIN_MATCH_COUNT = 10

        # 读取图片
        img_main = cv2.imread(template_path)
        img_template = cv2.imread(target_path)

        if img_main is None or img_template is None:
            raise ValueError("无法读取图片，请检查文件路径")

        # 转换为灰度图（可选）
        if gray_compare:
            img_main_gray = cv2.cvtColor(img_main, cv2.COLOR_BGR2GRAY)
            img_template_gray = cv2.cvtColor(img_template, cv2.COLOR_BGR2GRAY)
        else:
            img_main_gray = img_main
            img_template_gray = img_template

        # 初始化SIFT检测器
        sift = cv2.SIFT_create()

        # 检测关键点和描述符
        kp1, des1 = sift.detectAndCompute(img_main_gray, None)
        kp2, des2 = sift.detectAndCompute(img_template_gray, None)

        # FLANN匹配器
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des2, des1, k=2)

        # 筛选好的匹配点
        good_matches = []
        for m, n in matches:
            if m.distance < threshold * n.distance:
                good_matches.append(m)
        print("匹配到点数：{}".format(len(good_matches)))
        if len(good_matches) > MIN_MATCH_COUNT:
            src_pts = np.float32([kp2[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp1[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            matchesMask = mask.ravel().tolist()

            h, w = img_template_gray.shape
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            dst = cv2.perspectiveTransform(pts, M)

            x = int(min([p[0][0] for p in dst]))
            y = int(min([p[0][1] for p in dst]))
            width = int(max([p[0][0] for p in dst]) - x)
            height = int(max([p[0][1] for p in dst]) - y)
            similarity = len(good_matches) / len(matches)

            location = {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "similarity": similarity
            }

            if display:
                img_main_color = img_main_gray.copy()
                img2 = cv2.polylines(img_main_color, [np.int32(dst)], True, (0, 255, 0), 2, cv2.LINE_AA)

                # 创建一个可调整大小的窗口
                cv2.namedWindow('Matching Result', cv2.WINDOW_NORMAL)

                # 设置窗口的初始大小，这里设置为 800x600，你可以根据需要修改
                cv2.resizeWindow('Matching Result', 800, 450)

                # 显示匹配结果
                cv2.imshow('Matching Result', img2)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

            print("获取到图像匹配信息：{}".format(location))
            return location
        else:
            print("图像匹配失败")
            return None

    def compress_image(self, pic_path, out_path, ratio: float = 0.4):
        """
        压缩图片
        :param pic_path: 压缩源文件
        :param out_path: 压缩文件保存地址
        :param ratio: 分辨率比例
        :return:
        """
        image = cv2.imread(pic_path)
        res = cv2.resize(image, (int(image.shape[1] * ratio), int(image.shape[0] * ratio)),
                         interpolation=cv2.INTER_AREA)
        cv2.imwrite(out_path, res)

    def crop_image_output(self, input_path, output_path, x, y, width, height):
        """
        此函数用于裁剪图片，保存裁剪后的图片
        :param input_path: 输入图片的文件路径
        :param output_path: 裁剪后图片的保存路径
        :param x: 裁剪区域左上角的 x 坐标
        :param y: 裁剪区域左上角的 y 坐标
        :param width: 裁剪区域的宽度
        :param height: 裁剪区域的高度
        """
        try:
            # 读取图片
            image = cv2.imread(input_path)
            if image is None:
                print("无法读取图片，请检查文件路径。")
                return
            # 裁剪图片
            cropped_image = image[y:y + height, x:x + width]
            # 保存裁剪后的图片
            cv2.imwrite(output_path, cropped_image)
            print(f"裁剪后的图片已保存到 {output_path}")
        except Exception as e:
            print(f"发生错误: {e}")

    def crop_image_data(self, input_path, x, y, width, height):
        """
        此函数用于裁剪图片，直接输出图片数据
        :param input_path: 输入图片的文件路径
        :param x: 裁剪区域左上角的 x 坐标
        :param y: 裁剪区域左上角的 y 坐标
        :param width: 裁剪区域的宽度
        :param height: 裁剪区域的高度
        :return: 裁剪后的图片数组
        """
        try:
            # 读取图片
            image = cv2.imread(input_path)
            if image is None:
                print("无法读取图片，请检查文件路径。")
                return None
            # 裁剪图片
            cropped_image = image[y:y + height, x:x + width]
            return cropped_image
        except Exception as e:
            print(f"发生错误: {e}")
            return None

    def ocr(self, image_path):
        """
        OCR识别
        """
        start_time = time.time()
        engine = RapidOCR()
        result, elapse = engine(image_path)
        end_time = time.time()
        print("本次识别耗时: {} s".format(end_time - start_time))
        str_list = []  # 将每行的文字依次放入列表
        str_point = {}
        strings = ""  # 拼接识别到的字符串
        use_time2 = 0
        for res in result:
            str_list.append(res[1])
            strings += res[1]
            use_time2 += res[2]
        lines = len(str_list)
        ocr_info = {"str_list": str_list, "strings": strings, "lines": lines}
        # print(ocr_info)
        return ocr_info

    def get_dominant_color(self, image_path, k=5):
        """
        获取图片的主要颜色
        参数:
            image_path: 图片路径
            k: 聚类数量 (默认5种主要颜色)
        返回:
            dominant_colors: 按比例排序的 RGB 颜色列表
        """
        # 读取图片并转换颜色空间
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 调整图片尺寸加速处理
        resized_image = cv2.resize(image, (200, 200), interpolation=cv2.INTER_AREA)

        # 将图片转换为二维数组
        pixels = resized_image.reshape((-1, 3))

        # 使用 K-Means 聚类寻找主要颜色
        kmeans = KMeans(n_clusters=k, n_init=10)
        kmeans.fit(pixels)

        # 获取颜色分布比例
        counts = Counter(kmeans.labels_)
        total = sum(counts.values())

        # 按比例排序颜色
        sorted_colors = sorted(
            [(color, count / total) for color, count in zip(kmeans.cluster_centers_, counts.values())],
            key=lambda x: x[1],
            reverse=True
        )

        return [color for color, _ in sorted_colors]

    def rgb_to_color_name(self, rgb):
        """
        将 RGB 值转换为颜色名称
        参数:
            rgb: 包含 R, G, B 值的元组 (0-255)
        返回:
            颜色名称字符串
        """
        # 定义颜色范围 (HSV 空间更易识别颜色)
        hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]

        hue = hsv[0]

        # 颜色阈值定义
        color_ranges = {
            "红色": ((0, 100, 100), (10, 255, 255)) or ((160, 100, 100), (180, 255, 255)),
            "橙色": ((11, 100, 100), (25, 255, 255)),
            "黄色": ((26, 100, 100), (35, 255, 255)),
            "绿色": ((36, 100, 100), (85, 255, 255)),
            "蓝色": ((86, 100, 100), (125, 255, 255)),
            "紫色": ((126, 100, 100), (150, 255, 255)),
            "粉色": ((151, 50, 100), (159, 255, 255)),
            "白色": ((0, 0, 200), (180, 30, 255)),
            "灰色": ((0, 0, 50), (180, 30, 200)),
            "黑色": ((0, 0, 0), (180, 255, 50))
        }

        # 检查颜色范围
        for color_name, (lower, upper) in color_ranges.items():
            if (lower[0] <= hue <= upper[0]):
                # 检查饱和度和明度
                if lower[1] <= hsv[1] <= upper[1] and lower[2] <= hsv[2] <= upper[2]:
                    return color_name
        return "其他颜色"

    def analyze_image_colors(self, image_path):
        """
        分析并显示图片颜色信息
        """
        # 获取主要颜色
        colors = self.get_dominant_color(image_path)
        if not colors:
            return False

        color_names = []
        # 打印结果
        print("主要颜色检测结果：")
        for i, color in enumerate(colors, 1):
            color_name = self.rgb_to_color_name(color)
            print(f"{i}. RGB: {tuple(map(int, color))} -> {color_name}")
            color_names.append(color_name)

        # # 可视化显示颜色
        # plt.figure(figsize=(10, 2))
        # for i, color in enumerate(colors):
        #     plt.subplot(1, len(colors), i + 1)
        #     plt.imshow([[tuple(map(int, color))]])
        #     plt.axis('off')
        #     plt.title(f"{self.rgb_to_color_name(color)}\n{tuple(map(int, color))}")
        # plt.show()
        return color_names


if __name__ == '__main__':
    from Global import *
    cv = CVFunction()
    debug_files_path = os.path.join(main_run_path, "debug_files")
    img1_path = os.path.join(debug_files_path, "img1.png")
    img2_path = os.path.join(debug_files_path, "img_computer.png")

    # -------------------  常规匹配，像素点匹配  ----------------------
    # print(img2_path)
    # cv_info = cv.find_image_position_pixel(template_path=img1_path, target_path=img2_path, gray_compare=True, display=True)
    # print(cv_info)

    # -------------------  常规匹配，特征点匹配  ----------------------
    # print(img2_path)
    # cv_info = cv.find_image_position_feature(template_path=img1_path, target_path=img2_path, gray_compare=True,
    #                                          display=True)
    # print(cv_info)

    # -------------------  裁剪图片并保存  ----------------------
    # output_path = os.path.join(debug_files_path, "output.png")
    # cv.crop_image_output(input_path=img1_path, output_path=output_path, x=1820, y=0, width=65, height=85)

    # -------------------  获取图片颜色  -------------------
    # img_red = os.path.join(debug_files_path, "red.png")
    # print(img_red)
    # cv.analyze_image_colors(image_path=img_red)

    # -------------------  OCR识别文字  -------------------
    output_path = os.path.join(debug_files_path, "txt_test.png")
    print("待识别图片位置：{}".format(output_path))
    ocr_res = cv.ocr(image_path=output_path)
    print(ocr_res)
