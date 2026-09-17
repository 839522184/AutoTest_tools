data = {
    "927c1d36ca92400b8a1f89630ff72929": {
        "name": "设置",
        "do_action": 'start_app(package_name="com.android.settings", activity_name="com.android.settings.Settings")',
        "location": {},
        "container": {},

        "67cfe1e952ca4e338d03f91f9c66ff50": {
            # 元素树名
            "name": "关于平板电脑",
            # 插入式脚本
            "do_action": "",
            "location_flag": "xpath",
            # 属性定位
            "location": {"resourceId": "",
                         "text": "关于平板电脑",
                         "description": ""},
            "xpath": '//*[@text="关于平板电脑"]',
            "image": {"image_path": "xxxxxx", "compare": 0.85},
            # 容器
            "container": {"resourceId": "com.android.settings:id/dashboard_container"},

            "5848adee814f46a4b8c389d8c796f411": {
                "name": "设备名称",
                "do_action": "",
                "location": {"resourceId": "android:id/title", "text": "设备名称"},
                "container": {"resourceId": "com.android.settings:id/content_frame"},
            },
            "df2ce4225e4a4d669211d1d9ef9eae19": {
                "name": "法律信息",
                "do_action": "",
                "location": {"resourceId": "android:id/title", "text": "法律信息"},
                "container": {"resourceId": "com.android.settings:id/content_frame"},
            },
        }
    },
    "AppList": {},
    "控制中心": {},
    "Dock": {},
    "状态栏": {},
    "负一屏": {},
    "Launcher": {},
}
import tkinter as tk
from tkinter import ttk

# 存储节点 ID 和数据映射
node_data_map = {}


def insert_node(tree, parent, key, value):
    """递归插入元素树"""
    if isinstance(value, dict) and "name" in value:
        node_text = f"{value['name']} ({key})"
    else:
        node_text = str(key)

    current_node = tree.insert(parent, "end", text=node_text)
    node_data_map[current_node] = (key, value)

    if isinstance(value, dict):
        for k, v in value.items():
            if k in ["name", "do_action", "location_flag", "location", "xpath", "image", "container"]:
                continue
            insert_node(tree, current_node, k, v)


def expand_all(tree, item=""):
    """递归完全展开所有节点"""
    children = tree.get_children(item)
    for child in children:
        tree.item(child, open=True)
        expand_all(tree, child)


def update_right_display(from_tree_click=False):
    """核心联动修复：支持元组解包，准确读取选中的节点信息"""
    selected_items = tree.selection()
    if not selected_items:
        return

    # 【核心修复】tree.selection() 返回的是元组，取第 0 个元素才是真实的节点 ID
    node_id = selected_items[0]

    if node_id not in node_data_map:
        return

    key, val = node_data_map[node_id]
    is_dict = isinstance(val, dict)

    # 1. 刷新节点基本信息标题
    info_text.set(f"节点 ID: {key}   |   节点名称: {val.get('name', '（无）') if is_dict else '（分类）'}")

    # 2. 如果是从树节点点击触发，优先读取数据中的 location_flag 并同步单选框状态
    if from_tree_click and is_dict:
        flag = val.get("location_flag", "location")
        if flag not in ["location", "xpath", "image"]:
            flag = "location"
        mode_var.set(flag)

    # 3. 动态拼接并展示定位与容器信息
    attr_box.delete("1.0", tk.END)
    if is_dict:
        current_mode = mode_var.get()

        # 组装对应的定位文本
        if current_mode == "xpath":
            xpath_val = val.get("xpath", "")
            loc_text = f"🌐 XPath 定位参数:\n{xpath_val if xpath_val else '（空）'}"
        elif current_mode == "image":
            img_val = val.get("image", {})
            loc_text = f"🖼️ Image 图片定位参数:\n{img_val if img_val else '（空）'}"
        else:
            loc_val = val.get("location", {})
            loc_text = f"📍 Location 属性定位参数:\n{loc_val if loc_val else '（空）'}"

        con_val = val.get("container", {})
        con_text = f"\n\n📦 Container 容器参数:\n{con_val if con_val else '（空）'}"

        attr_box.insert(tk.END, loc_text + con_text)
    else:
        attr_box.insert(tk.END, "无定位与容器属性")

    # 4. 下方展示：Python 代码块
    code_box.delete("1.0", tk.END)
    if is_dict and val.get("do_action"):
        code_box.insert(tk.END, val["do_action"])
    else:
        code_box.insert(tk.END, "# 该节点没有关联的 Python 代码")


def on_tree_select(event):
    """当点击左侧树节点时"""
    update_right_display(from_tree_click=True)


def on_mode_change():
    """当手动切换右上方单选按钮时"""
    update_right_display(from_tree_click=False)


# 2. 创建主窗口
root = tk.Tk()
root.title("UI 元素树与代码查看器 (修正版)")
root.geometry("1000x650")

# 3. 左右主分栏
main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
main_paned.pack(fill="both", expand=True, padx=10, pady=10)

# --- 左侧：元素层级树 ---
left_frame = ttk.Frame(main_paned)
main_paned.add(left_frame, weight=1)

tree = ttk.Treeview(left_frame)
tree.heading("#0", text="UI 元素层级树", anchor="w")
tree.pack(fill="both", expand=True)

scrollbar = ttk.Scrollbar(tree, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# --- 右侧：详细内容展示区 ---
right_frame = ttk.Frame(main_paned)
main_paned.add(right_frame, weight=2)

# 顶部工具栏（横向容纳 节点信息 和 三个单选按钮）
top_bar = ttk.Frame(right_frame)
top_bar.pack(fill="x", pady=(0, 10))

info_text = tk.StringVar(value="请在左侧选择一个节点")
lbl_info = ttk.Label(top_bar, textvariable=info_text, font=("Arial", 10, "bold"), foreground="#003366")
lbl_info.pack(side="left", anchor="w")

# 单选按钮容器（靠右对齐）
radio_frame = ttk.Frame(top_bar)
radio_frame.pack(side="right", anchor="e")

ttk.Label(radio_frame, text="定位方式(三选一):", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 5))
mode_var = tk.StringVar(value="location")  # 默认选中 location

r_location = ttk.Radiobutton(radio_frame, text="location", value="location", variable=mode_var, command=on_mode_change)
r_location.pack(side="left", padx=5)

r_xpath = ttk.Radiobutton(radio_frame, text="xpath", value="xpath", variable=mode_var, command=on_mode_change)
r_xpath.pack(side="left", padx=5)

r_image = ttk.Radiobutton(radio_frame, text="image", value="image", variable=mode_var, command=on_mode_change)
r_image.pack(side="left", padx=5)

# 创建右侧的内部上下分栏
right_paned = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
right_paned.pack(fill="both", expand=True)

# 3.1 上方组件：元素信息框
top_info_frame = ttk.Frame(right_paned)
right_paned.add(top_info_frame, weight=1)

lbl_attr = ttk.Label(top_info_frame, text="⚙️ 元素定位信息:", font=("Arial", 9, "bold"))
lbl_attr.pack(anchor="w", pady=(0, 2))
attr_box = tk.Text(top_info_frame, font=("Consolas", 10), bg="#fcfcfc", fg="#333333")
attr_box.pack(fill="both", expand=True)

# 3.2 下方组件：Python 代码块展示框
bottom_code_frame = ttk.Frame(right_paned)
right_paned.add(bottom_code_frame, weight=2)

lbl_code = ttk.Label(bottom_code_frame, text="🐍 do_action (Python 代码块):", font=("Arial", 9, "bold"))
lbl_code.pack(anchor="w", pady=(5, 2))
code_box = tk.Text(bottom_code_frame, font=("Consolas", 10), bg="#f4fbf4", fg="#006600")
code_box.pack(fill="both", expand=True)

# 4. 数据导入与初始化
for root_key, root_value in data.items():
    insert_node(tree, "", root_key, root_value)

expand_all(tree)

# 5. 绑定事件
tree.bind("<<TreeviewSelect>>", on_tree_select)

# 6. 进入主循环
root.mainloop()