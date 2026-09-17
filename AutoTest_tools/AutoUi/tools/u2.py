# !/usr/bin/python
# -*-coding:utf-8 -*-


import subprocess
import re
import uiautomator2 as u2
import time
import os

# -------------- debug
from locations.UiLocations import location_tree


# ----------------------------------


class SetDevice:

    def __init__(self, device_name=None):
        if device_name:
            self.device_name = device_name
        else:
            self.device_name = self.get_device_name()
        self.device = self.link_device()

    def get_device_name(self):
        """
        获取adb devices
        :return:
        """
        # 如果没有传入device_name则adb devices取第一个
        result = subprocess.run(["adb", "devices"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        res = re.findall("\n(.*)\s*device", result.stdout)
        if not res:
            assert False, "获取adb device失败"
        device_name = res[0].strip()
        return device_name

    def link_device(self):
        """
        连接Android设备
        :return:
        """
        try:
            return u2.connect(self.device_name)
        except Exception as e:
            print("连接Android设备失败")
            print(e)


class Ui2Base(SetDevice):
    def __init__(self, device_name=None):
        super().__init__(device_name)
        self.element = {}

    def start_app(self, package_name, activity_name):
        command = f"adb -s {self.device_name} shell am start -n {package_name}/{activity_name}"
        try:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            print(f"{package_name}/{activity_name} 启动成功")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"{package_name}/{activity_name} 启动失败: {e.stderr}")

    def wait_element(self, selectors: dict, timeout=5):
        """
        等待组件出现，timeout未出现返回None
        :param selectors:
        :param timeout:
        :return:
        """
        wait = timeout
        while wait >= 0:
            element = self.find_element(selectors)
            if element.exists():
                print(f"组件出现 {selectors}")
                return element
            time.sleep(0.5)
            wait -= 0.5
        print(f"未查找到组件 {selectors}")
        return None

    def find_element(self, selectors: dict, img_path=None, time_out=5):
        """
        查找组件
        :param ele_locator:
        :param use_type:
        :param img_path:
        :return:
        """
        print(f"find selectors {selectors}")
        # 每次执行当前函数就初始化一次element
        self.element = {"element": ""}
        # 入参限制
        types = ["resourceId", "text", "description", "xpath"]
        for use_type in selectors.keys():
            assert use_type in types, "组件查找方式异常，当前不支持的查找类型：{}".format(use_type)

        if img_path:
            # 图像匹配
            pass
        else:
            if "xpath" in selectors.keys():
                elements = self.device.xpath(selectors.get("xpath")).all()
                element = None
                if elements:
                    element = elements[0]  # 取第一个
            else:
                # 组件查找
                element = self.device(**selectors)

            if element.exists():
                self.element.update({"element": element})
                self.element.update(element.info)
            return element
            # print(self.element)

    def click(self):
        pass

    def press(self, action):
        """
        按键操作
        :param action:
        :return:
        """
        action_dict = {"home": "home",
                       "back": "back",
                       "left": "左键",
                       "right": "右键",
                       "up": "上键",
                       "down": "下键",
                       "center": "选中",
                       "menu": "菜单",
                       "search": "搜索",
                       "enter": "enter",
                       "delete": "删除",
                       "recent": "最近任务",
                       "volume_up": "音量+",
                       "volume_down": "音量-",
                       "volume_mute": "静音",
                       "camera": "相机",
                       "power": "电源",
                       }
        alphabet = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
                    "U", "V", "W", "X", "Y", "Z"]
        if action in action_dict.keys() or action in alphabet:
            self.device.press(action)
            print(f"press {action}")
        else:
            assert KeyError, "请检查入参action，不存在此按键"

def get_toast(self):
    """
    获取Toast信息
    """
    toasts = []
    os.popen("timeout 5 adb -s {} shell logcat -c".format(self.device_name)).readlines()
    time.sleep(1)

    res = os.popen(
        "timeout 5 adb -s {} shell logcat | grep 'Toast'".format(self.device_name)).readlines()
    print(f"获取到输入语：{res}")
    for info in res:
        re_info = re.findall(r"message：(.+)", info)
        if re_info:
            toasts.append(re_info[0].strip())

class Goto(Ui2Base):

    def location_init(self, location_path):
        """
        goto前，location初始化操作
        :param location_path:
        :return:
        """
        run_list = []
        # 拆分路径，用于提取元素定位信息
        location_names = location_path.split("/")
        for name_index, action_name in enumerate(location_names):
            # 当前操作的元素信息
            action_dict = location_tree.get(action_name)
            run_list.append(action_dict)
        return run_list

    def get_element_path(self, target_key):
        """
        依据唯一ID逆推嵌套路径
        :param target_key:
        :return:
        """

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

        return traverse(location_tree, [])

    def run_action(self, action):
        """
        执行导航过程中穿插的操作
        :param action:
        :return:
        """
        print(action)
        # self.start_app()
        eval(f"self.{action}")

    def run_find_element_for_container(self, parent_element, selector: dict):
        """
        在指定元素范围内查找元素，支持滑动查找
        :param parent_element: 父元素对象
        :param selector: 查找元素的选择器，例如 text='目标文本', resourceId='com.example:id/button'
        :return: 找到的元素对象，如果未找到则返回 None
        """
        try:
            # 获取父元素的边界信息
            parent_bounds = parent_element.info.get('bounds')
            if not parent_bounds:
                print("无法获取父元素的边界信息")
                return None

            def check_elements():
                # 获取屏幕上所有符合选择器的元素
                all_elements = parent_element.child(**selector)
                # 筛选出在父元素范围内的元素
                for element in all_elements:
                    element_bounds = element.info.get('bounds')
                    if element_bounds:
                        if (element_bounds['left'] >= parent_bounds['left'] and
                                element_bounds['right'] <= parent_bounds['right'] and
                                element_bounds['top'] >= parent_bounds['top'] and
                                element_bounds['bottom'] <= parent_bounds['bottom']):
                            return element
                return None

            def check_bounds():
                texts = []
                # 获取组件下的所有子元素
                children = parent_element.child()
                for child in children:
                    if child.info.get('text'):
                        texts.append(child.info['text'])
                    if child.info.get('contentDescription'):
                        texts.append(child.info['contentDescription'])
                    if len(texts) >= 4:
                        break
                # 过滤掉数字，规避计时类组件影响判断
                res_str = "".join(texts).replace("1", "").replace("2", "").replace("3", "").replace("4", "").replace(
                    "5", "").replace("6", "").replace("7", "").replace("8", "").replace("9", "").replace("0", "")
                return res_str

            # 先向上滑动查找
            while True:
                result = check_elements()
                if result:
                    return result
                start_str = check_bounds()
                parent_element.swipe("up")
                end_str = check_bounds()
                if start_str == end_str:
                    break

            # 若向上未找到，向下滑动查找
            while True:
                result = check_elements()
                if result:
                    return result
                start_str = check_bounds()
                parent_element.swipe("down")
                end_str = check_bounds()
                if start_str == end_str:
                    break
            return None
        except Exception as e:
            print(f"查找元素时出现错误: {e}")
            return None

    def goto(self, l_id, location_path=None):
        """
        :param l_id: 唯一ID
        :param location_path: "我的设备/全部参数与信息/xxx"，主要起到标注作用
        :return: 定位到的元素
        """
        run_list = self.get_element_path(l_id)

        now_uid_dict = None
        # 遍历执行每一步操作，实现导航
        for name_index, uid in enumerate(run_list):
            if not now_uid_dict:
                now_uid_dict = location_tree.get(uid)
            else:
                now_uid_dict = now_uid_dict.get(uid)

            # 当前操作的元素信息
            action_dict = now_uid_dict.get("do_action")
            location_dict = now_uid_dict.get("location")
            container = now_uid_dict.get("container")

            if action_dict:
                # 执行前操作
                self.run_action(action=action_dict)
            if location_dict:
                if container:
                    # 执行从容器查找元素操作
                    print(f"容器 {container} 内查找 {location_dict}")
                    parent_element = self.find_element(container)
                    element = self.run_find_element_for_container(parent_element=parent_element, selector=location_dict)
                else:
                    # 不从容器查找
                    element = self.find_element(location_dict)

                # 找到元素后的操作
                if name_index + 1 == len(run_list):
                    element = ""
                    # 最后返回定位到的页面元素
                    return element
                else:
                    # 非最后一个元素，主动执行点击操作
                    element.click()
            if not action_dict and not location_dict:
                assert False, "组件必须存在操作项"


if __name__ == '__main__':
    # device = u2.connect("emulator-5554")
    # parent_ele = device(resourceId="com.android.settings:id/dashboard_container")
    # eles = parent_ele.child(text="关于平板电脑")
    # eles.click()
    # for ele in eles:
    #     print(ele.info)

    # ua = Ui2Base("emulator-5554")
    # ua.start_app(package_name="com.android.settings", activity_name="com.android.settings.Settings")
    # phone_info = {"resourceId": "android:id/title", "text": "关于平板电脑"}
    # phone_name = {"resourceId": "android:id/title", "text": "设备名称"}
    # ele = ua.find_element(phone_info)
    # ele.click()
    # ele = ua.find_element(phone_name)
    # ele.click()

    gt = Goto()
    # gt.press("home")
    # gt.goto(l_id="df2ce4225e4a4d669211d1d9ef9eae19", location_path="手机设置/关于平板电脑/设备名称")

    # title_local = {"resourceId": "android:id/title", "text": "关于平板电脑"}
    # element = gt.wait_element(title_local, timeout=2)
