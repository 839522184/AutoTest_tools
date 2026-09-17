import platform
import os
import psutil
import subprocess
import time

if platform.system() == "Windows":
    # win32使用300版本，否则会报dll错误
    try:
        os.system("pip install pywin32==300")
    except Exception as e:
        print('pywin32安装失败')
    import winreg
    from pywinauto.application import Application
    from pywinauto import Desktop
    from pywinauto import backends
    
"""
工具推荐：
https://www.autoitscript.com/site/autoit/downloads/
安装Windows SDK过程耗时比较长, 安装完成后在文件夹内搜索 inspect, 根据当前操作系统选择对应的GUI工具

window() 方法的常用参数:
    title: 窗口的标题。
    title_re: 窗口标题的正则表达式。
    class_name: 窗口的类名。
    class_name_re: 窗口类名的正则表达式。
    control_id: 控件的 ID。
    handle: 窗口的句柄。
    found_index: 如果有多个窗口匹配，指定要选择的窗口的索引（从 0 开始）。
    backend: 指定使用的后端（例如 "win32" 或 "uia"）。

child_window() 方法的常用参数:
    title: 窗口的标题。
    control_type: 控件的类型，例如 Button、Edit、Text 等。
    class_name: 窗口的类名。
    auto_id: 自动生成的控件 ID。
    found_index: 在找到的多个控件中选择特定的一个（从 0 开始）。
    best_match: 最佳匹配的控件名称。
    handle: 窗口句柄。
    
descendants() 方法的常用参数:
    depth: 指定搜索的深度。默认值为 None, 表示搜索所有深度的子控件。
    filter: 一个字典，用于过滤子控件。字典的键是控件的属性名，值是属性的期望值。只有满足这些条件的控件才会被返回。
    active_only: 一个布尔值，指定是否只返回活动的控件。默认值为 False。
    control_type: 指定控件的类型。可以是一个字符串或一个字符串列表，表示控件的类型名称（例如 "Button", "Edit" 等）。
    title: 指定控件的标题。可以是一个字符串或一个字符串列表，表示控件的标题。
    class_name: 指定控件的类名。可以是一个字符串或一个字符串列表，表示控件的类名。

    
菜单导航：
菜单控件.menu_select("File->Open")
"""


class WinUiAuto:

    def __init__(self, app_path, proc_name) -> None:
        self.proc_name = proc_name  # 
        self.app_path = app_path
        self.aw = self.get_main_window()
        
    # 查看所有可用后端
    def print_backends(self):
        """
        win32/uia/win32+uia
        """
        print(backends.registry.backends)
        
    # 聚焦窗口到前台
    def foreground_window(self, window):
        """
        传入有效窗口
        """
        # 将窗口置于前台
        # SetForegroundWindow(window_handle)
        # 聚焦窗口
        window.set_focus()
        # 判断是否成功聚焦
        if window.has_focus():
            print("窗口聚焦成功")
            return True
        else:
            print("窗口聚焦失败")
            return False
    
    # 关闭窗口
    def clouse_aw(self):
        self.aw.clouse()
    
    # 查找元素
    def find_window(self, el_type, el_info):
        if el_type == "title":
            element = self.aw.window(title=el_info)
        elif el_type == "class_name":
            element = self.aw.window(class_name=el_info)
        elif el_type == "control_id":
            element = self.aw.window(control_id=el_info)
        else:
            raise "不支持的传参：{}".format(el_type)
        return element
    
    # 查找元素，模糊匹配
    def find_window_re(self, el_type, el_info):
        if el_type == "title_re":
            element = self.aw.window(title_re=el_info)
        elif el_type == "class_name_re":
            element = self.aw.window(class_name_re=el_info)
        else:
            raise "不支持的传参：{}".format(el_type)
        return element
    
    # 查找子元素
    def find_child_window(self, p_el, el_type, el_info):
        if el_type == "title":
            element = p_el.child_window(title=el_info)
        elif el_type == "auto_id":
            element = p_el.child_window(auto_id=el_info)
        elif el_type == "class_name":
            element = p_el.child_window(class_name=el_info)
        elif el_type == "control_type":
            element = p_el.child_window(control_type=el_info)
        else:
            raise "不支持的传参：{}".format(el_type)
        return element
    
    # 获取控件下的所有子控件
    def find_all_child(self, p_el):
        elements = p_el.descendants()
        return elements
    
    # 获取子控件
    def find_child_element(self, p_el, el_type, el_info):
        """
        案例：
            filter: descendants(filter={"title": "Edit"})  过滤title为Edit的元素, 可追加过滤字段, 比较类似xpath中的//*[... and ...]格式
            control_type: descendants(control_type="Button")  过滤所有按钮
        """
        if el_type == "title":
            element = p_el.descendants(title=el_info)
        elif el_type == "class_name":
            element = p_el.descendants(class_name=el_info)
        elif el_type == "filter":
            element = p_el.descendants(filter=el_info)
        elif el_type == "control_type":
            element = p_el.descendants(control_type=el_info)
        else:
            raise "不支持的传参：{}".format(el_type)
        return element
    
    # 菜单导航
    def menu_select(self, mw, menu_str):
        """
        menu_select("File->Open")
        """
        mw.menu_select(menu_str)
    
    # 点击元素
    def click_element(self, el1, el2=None):
        """
        如果: el1传参为可点击的元素, 则执行点击操作
        否则: 进行常规查找元素，点击
        """
        if not isinstance(el1, str):
            el1.click_input()
        else:
            element = self.find_window(el_type=el1, el_info=el2)
            element.click_input()
            
    # 输入信息
    def send_keys(self, el, info, pause=0.1):
        """
        方法可发送组合键, 详情百度
        """
        print("输入字符串: {}".format(info))
        for l in info:
            el.type_keys(l)
            time.sleep(pause)
        # el.type_keys(info, pause=None, with_spaces=False)  # 每输入一个字符等待pause秒, with_spaces空格相关配置，暂不清晰
        # el.send_keys(info, pause=0.1)  
    
    # 最小化桌面窗口
    @staticmethod
    def mini_all():
        # 获取当前桌面上的所有窗口
        windows = Desktop(backend="win32").windows()
        # 遍历所有窗口
        for w in windows:
            # 判断窗口是否可见以及是否已经最小化
            if w.is_visible() and not w.is_minimized():
                try:
                    # 尝试最小化窗口
                    w.minimize()
                except Exception as e:
                    # 如果出现错误，打印错误信息（例如，一些窗口可能无法被最小化）
                    print(f"Error minimizing window: {e}")
    
    
    # 根据进程名获取进程id
    @staticmethod
    def get_procid_byname(proc_name):
        all_processes = list(psutil.process_iter(['pid', 'name']))
        process_list = [proc.info for proc in all_processes if proc.info['name'] == proc_name]
        process_ids = [proc_info['pid'] for proc_info in process_list]
        return process_ids
    
    # 启动app
    def start_app(self):
        p = subprocess.Popen(self.app_path, shell=True)
        count = 300
        while len(self.get_procid_byname(self.proc_name)) == 0 and count > 0:
            time.sleep(1)
            count -= 1
    
    # 获取窗口对象
    def get_main_window(self):
        self.mini_all()
        if len(self.get_procid_byname(self.proc_name)) == 0:
            # 没有ui进程的情况
            self.start_app()  # 启动app
            app = Application(backend="uia").connect(process=self.get_procid_byname(self.proc_name)[0])
            time.sleep(5)
            main_window = app.window(title='')
            main_window.set_focus()  # 聚焦到当前窗口
            main_window.set_focus()
            return main_window
        else:
            # 存在ui进程则关闭进程后从新启动
            app = Application(backend="uia").connect(process=self.get_procid_byname(self.proc_name)[0])
            main_window = app.window(title='')
            main_window.close()
            time.sleep(1)
            p = subprocess.Popen(self.app_path, shell=True)
            count = 10
            while len(self.get_procid_byname(self.proc_name)) == 0 and count > 0:
                time.sleep(1)
                count -= 1
            app = Application(backend="uia").connect(process=self.get_procid_byname(self.proc_name)[0])
            time.sleep(5)
            main_window = app.window(title='终端防护中心')
            main_window.set_focus()  # 聚焦到当前窗口
            main_window.set_focus()
            return main_window


if __name__ == '__main__':
    PotPlayer = r"D:\APP\PotPlayer\PotPlayerMini64.exe"
    test_app = WinUiAuto(app_path=PotPlayer, proc_name="PotPlayerMini64.exe")









