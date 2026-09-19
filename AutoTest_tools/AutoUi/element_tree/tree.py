import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from element_tree.get_uuid import generate_unique_id

# 存储节点 iid -> (key, value) 映射
node_data_map = {}


def _log(msg):
    """打印操作日志到 PyCharm 控制台，带毫秒级时间戳。"""
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}", flush=True)

# ------------------------ ** 变量在此处存放 **
# 元素树数据所在包与目录
DATA_PACKAGE = "element_tree.element_tree_data"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "element_tree_data")
SAVE_HEADER = "# 本文件由 tree.py 自动生成/覆盖保存\n"
DEFAULT_MODULE = "Demo_data"   # 默认加载的元素树模块名
# ------------------------ ** **

# 运行时状态：当前加载的元素树字典、模块对象、字典变量名
data = {}
current_mod = None
current_dict_name = "data"


def insert_node(tree_widget, parent, key, value):
    """递归插入元素树"""
    if isinstance(value, dict) and "name" in value:
        node_text = f"{value['name']} ({key})"
    else:
        node_text = str(key)

    current_node = tree_widget.insert(parent, "end", text=node_text)
    node_data_map[current_node] = (key, value)

    if isinstance(value, dict):
        for k, v in value.items():
            if k in ["name", "do_action", "location_flag", "location", "xpath", "image", "container"]:
                continue
            insert_node(tree_widget, current_node, k, v)


def expand_all(tree_widget, item=""):
    """递归完全展开所有节点"""
    children = tree_widget.get_children(item)
    for child in children:
        tree_widget.item(child, open=True)
        expand_all(tree_widget, child)


def flatten_props(val, mode="location"):
    """把节点字典按当前定位方式拍平成 (属性名, 值) 行，供 Excel 风格表格展示。
    始终展示 name；container 在 location / xpath 模式下展示，image 模式下不展示。
    do_action 不在本表展示，统一在右下方代码框显示。"""
    rows = []
    if not isinstance(val, dict):
        return rows

    rows.append(("name", str(val.get("name", ""))))

    if mode == "xpath":
        rows.append(("xpath", str(val.get("xpath", ""))))
    elif mode == "image":
        img = val.get("image", {})
        if isinstance(img, dict) and img:
            for k, v in img.items():
                rows.append((f"image.{k}", str(v)))
        elif img:
            rows.append(("image", str(img)))
    else:  # location
        loc = val.get("location", {})
        if isinstance(loc, dict) and loc:
            for k, v in loc.items():
                rows.append((f"location.{k}", str(v)))
        elif loc:
            rows.append(("location", str(loc)))

    # 容器信息：location / xpath 模式下展示，image 模式下不展示
    if mode != "image":
        con = val.get("container", {})
        if isinstance(con, dict) and con:
            for k, v in con.items():
                rows.append((f"container.{k}", str(v)))
        elif con:
            rows.append(("container", str(con)))

    return rows


# ============ 元素树模块（多项目）加载 ============

def list_data_modules():
    """扫描 DATA_DIR 下的 .py 文件，返回可用元素树模块名列表。"""
    names = []
    if not os.path.isdir(DATA_DIR):
        return names
    for fname in sorted(os.listdir(DATA_DIR)):
        if fname.endswith(".py") and not fname.startswith("_") and fname != "__init__.py":
            names.append(fname[:-3])
    return names


def _find_tree_dict(mod):
    """在模块里找到元素树字典及其变量名（第一个非下划线开头的 dict）。"""
    for name, obj in vars(mod).items():
        if name.startswith("_"):
            continue
        if isinstance(obj, dict):
            return name, obj
    return None, None


def load_data_module(mod_name):
    """动态加载指定元素树模块，重建左侧树并清空右侧面板。"""
    global data, current_mod, current_dict_name
    try:
        import importlib
        mod = importlib.import_module(f"{DATA_PACKAGE}.{mod_name}")
        importlib.reload(mod)
    except Exception as e:
        messagebox.showerror("加载失败", f"无法加载 {mod_name}: {e}", parent=root)
        return False

    dict_name, tree = _find_tree_dict(mod)
    if dict_name is None:
        messagebox.showerror("加载失败", f"{mod_name} 里没找到元素树字典", parent=root)
        return False

    current_mod = mod
    current_dict_name = dict_name
    data = tree

    _log(f"加载元素树模块: {mod_name} (字典变量名={dict_name}, 顶层节点数={len(data)})")

    element_tree.delete(*element_tree.get_children())
    node_data_map.clear()
    for k, v in data.items():
        insert_node(element_tree, "", k, v)
    expand_all(element_tree)

    prop_table.delete(*prop_table.get_children())
    code_box.delete("1.0", tk.END)
    info_text.set("请在左侧选择一个节点")
    table_title.set("📋 组件属性表")
    status_var.set(f"📂 已加载元素树: {mod_name}")
    return True


def on_combo_select(event):
    mod_name = tree_combo.get()
    if mod_name:
        load_data_module(mod_name)


# ============ 右侧表格刷新与编辑 ============

def update_right_display(from_tree_click=False):
    """核心联动：刷新右侧 Excel 属性表与下方代码框"""
    selected_items = element_tree.selection()
    if not selected_items:
        return

    node_iid = selected_items[0]
    if node_iid not in node_data_map:
        return

    key, val = node_data_map[node_iid]
    is_dict = isinstance(val, dict)

    # 1. 顶部节点信息
    info_text.set(f"节点 ID: {key}   |   节点名称: {val.get('name', '（无）') if is_dict else '（分类）'}")

    # 2. 从树点击时同步定位方式单选框
    if from_tree_click and is_dict:
        flag = val.get("location_flag", "location")
        if flag not in ["location", "xpath", "image"]:
            flag = "location"
        mode_var.set(flag)

    # 3. 刷新 Excel 风格属性表（按当前定位方式 mode 切换内容）
    current_mode = mode_var.get()
    prop_table.delete(*prop_table.get_children())
    if is_dict:
        for idx, (attr, value) in enumerate(flatten_props(val, current_mode)):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            prop_table.insert("", "end", values=(attr, value), tags=(tag,))
        table_title.set(f"📋 组件属性表 — 当前定位方式: {current_mode}（双击值可编辑）")
    else:
        prop_table.insert("", "end", values=("（分类节点）", "无定位与容器属性"), tags=("evenrow",))
        table_title.set("📋 组件属性表")

    # 4. 下方 do_action 代码块
    code_box.delete("1.0", tk.END)
    if is_dict and val.get("do_action"):
        code_box.insert(tk.END, val["do_action"])
    else:
        code_box.insert(tk.END, "# 该节点没有关联的 Python 代码")


def commit_edit(attr, new_text):
    """把表格里编辑后的值写回底层 data 字典，并自动落盘。
    允许编辑：location / xpath / image / container 字段。"""
    sel = element_tree.selection()
    if not sel:
        return
    key, val = node_data_map.get(sel[0], (None, None))
    if not isinstance(val, dict):
        return

    # 记录旧值用于日志
    old_val = ""
    if attr == "xpath":
        old_val = val.get("xpath", "")
        val["xpath"] = new_text
    elif attr.startswith("location."):
        sub = attr.split(".", 1)[1]
        old_val = val.get("location", {}).get(sub, "")
        val.setdefault("location", {})[sub] = new_text
    elif attr.startswith("image."):
        sub = attr.split(".", 1)[1]
        old_val = val.get("image", {}).get(sub, "")
        val.setdefault("image", {})[sub] = new_text
    elif attr.startswith("container."):
        sub = attr.split(".", 1)[1]
        old_val = val.get("container", {}).get(sub, "")
        val.setdefault("container", {})[sub] = new_text
    else:
        return

    _log(f"修改组件 [{key}] 属性 {attr}: {old_val!r} -> {new_text!r}")

    update_right_display(from_tree_click=False)
    ok, msg = persist_data()
    if ok:
        status_var.set(f"✏️ 已更新 {attr} 并保存")
    else:
        status_var.set(f"⚠️ {attr} 已更新但保存失败: {msg}")


def on_prop_double_click(event):
    """双击右上表格「值」单元格进入编辑态。"""
    region = prop_table.identify("region", event.x, event.y)
    if region != "cell":
        return
    col_id = prop_table.identify_column(event.x)
    row_id = prop_table.identify_row(event.y)
    if not row_id or col_id != "#2":
        return  # 只允许编辑「值」列

    values = prop_table.item(row_id, "values")
    if not values:
        return
    attr = values[0]
    # location / xpath / image / container 字段可编辑，name 不可编辑
    if not (attr.startswith("location.") or attr == "xpath"
            or attr.startswith("image.") or attr.startswith("container.")):
        status_var.set("ℹ️ 该字段不可编辑（仅 location / xpath / image / container 可改）")
        return

    bbox = prop_table.bbox(row_id, col_id)
    if not bbox:
        return
    x, y, w, h = bbox
    cur = values[1] if len(values) > 1 else ""

    edit_var = tk.StringVar(value=cur)
    entry = ttk.Entry(prop_table, textvariable=edit_var, font=("Consolas", 10),
                      style="TEntry")
    entry.place(x=x, y=y, width=w, height=h)
    entry.focus_set()
    entry.select_range(0, tk.END)

    def commit(_ev=None):
        entry.destroy()
        commit_edit(attr, edit_var.get())

    def cancel(_ev=None):
        entry.destroy()

    entry.bind("<Return>", commit)
    entry.bind("<FocusOut>", commit)
    entry.bind("<Escape>", cancel)


# ============ 左侧树右键菜单 ============

def copy_component_id():
    sel = element_tree.selection()
    if not sel:
        return
    key, _ = node_data_map[sel[0]]
    root.clipboard_clear()
    root.clipboard_append(key)
    status_var.set(f"📋 已复制组件 ID: {key}")


def add_component():
    sel = element_tree.selection()
    if not sel:
        messagebox.showinfo("提示", "请先在左侧选中一个父节点", parent=root)
        return
    parent_iid = sel[0]
    key, val = node_data_map[parent_iid]
    if not isinstance(val, dict):
        messagebox.showwarning("无法添加", "该节点不是容器，无法添加子组件", parent=root)
        return

    name = simpledialog.askstring("添加组件", "请输入新组件名称:", parent=root)
    if not name:
        return
    new_id = generate_unique_id()
    new_node = {
        "name": name,
        "do_action": "",
        "location_flag": "location",
        "location": {"resourceId": "", "text": "", "description": ""},
        "xpath": "//*[]",
        "image": {"image_path": "", "compare": 0.85},
        "container": {"xpath": "//*[]"},
    }
    val[new_id] = new_node

    _log(f"新增组件: 父节点={key}, 新组件 ID={new_id}, 名称={name!r}")

    child_iid = element_tree.insert(parent_iid, "end", text=f"{name} ({new_id})")
    node_data_map[child_iid] = (new_id, new_node)
    element_tree.item(parent_iid, open=True)
    element_tree.selection_set(child_iid)
    update_right_display(from_tree_click=True)
    ok, msg = persist_data()
    if ok:
        status_var.set(f"➕ 已添加组件: {name} 并保存")
    else:
        status_var.set(f"⚠️ 已添加 {name} 但保存失败: {msg}")


def delete_component():
    sel = element_tree.selection()
    if not sel:
        return
    iid = sel[0]
    key, val = node_data_map[iid]
    name = val.get("name", key) if isinstance(val, dict) else key
    if not messagebox.askyesno("删除组件",
                              f"确认删除「{name}」及其所有子节点？\n（此操作会同步删除内存中的数据）",
                              parent=root):
        return

    parent_iid = element_tree.parent(iid)
    if parent_iid:
        _, pval = node_data_map.get(parent_iid, (None, None))
        if isinstance(pval, dict) and key in pval:
            del pval[key]
    else:
        if key in data:
            del data[key]

    element_tree.delete(iid)
    node_data_map.pop(iid, None)
    _log(f"删除组件: ID={key}, 名称={name!r}")
    ok, msg = persist_data()
    if ok:
        status_var.set(f"🗑️ 已删除组件: {name} 并保存")
    else:
        status_var.set(f"⚠️ 已删除 {name} 但保存失败: {msg}")


def show_tree_menu(event):
    iid = element_tree.identify_row(event.y)
    if iid:
        element_tree.selection_set(iid)
        element_tree.focus(iid)
    tree_menu.tk_popup(event.x_root, event.y_root)


# ============ 保存到文件 ============

def _format_py(obj, level=0):
    """把 data 字典格式成干净的 Python 字面量文本（4 空格缩进，每行一个键）。"""
    indent = "    " * level
    inner = "    " * (level + 1)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        parts = []
        for k, v in obj.items():
            parts.append(f"{inner}{k!r}: {_format_py(v, level + 1)}")
        return "{\n" + ",\n".join(parts) + "\n" + indent + "}"
    return repr(obj)


def persist_data():
    """把当前 data 字典写回当前选中模块的 .py 文件。返回 (ok, msg)。"""
    try:
        path = current_mod.__file__
        if path.endswith((".pyc", ".pyo")):
            path = path[:-1]
        with open(path, "w", encoding="utf-8") as f:
            f.write(SAVE_HEADER)
            f.write(f"{current_dict_name} = " + _format_py(data) + "\n")
        _log(f"保存成功 -> {path}")
        return True, path
    except Exception as e:
        _log(f"保存失败: {e}")
        return False, str(e)


def save_to_file():
    ok, msg = persist_data()
    if ok:
        status_var.set(f"💾 已保存到 {msg}")
    else:
        messagebox.showerror("保存失败", msg, parent=root)


def reload_tree():
    """重新加载当前下拉框选中的元素树模块。"""
    mod_name = tree_combo.get()
    if mod_name:
        _log(f"手动刷新元素树: {mod_name}")
        load_data_module(mod_name)


def on_tree_select(event):
    update_right_display(from_tree_click=True)


def on_mode_change():
    """手动切换右上定位方式时，把选择写回当前节点的 location_flag 并保存。"""
    sel = element_tree.selection()
    if sel:
        key, val = node_data_map.get(sel[0], (None, None))
        if isinstance(val, dict):
            chosen = mode_var.get()
            old_flag = val.get("location_flag", "location")
            if old_flag != chosen:
                val["location_flag"] = chosen
                _log(f"组件 [{val.get('name','?')} ({key})] 定位方式 {old_flag} -> {chosen}")
                ok, msg = persist_data()
                if ok:
                    status_var.set(f"🏷️ 已将定位方式记为 {chosen} 并保存")
                else:
                    status_var.set(f"⚠️ 已切换 {chosen} 但保存失败: {msg}")
    update_right_display(from_tree_click=False)


# ============ 主窗口 ============
root = tk.Tk()
root.title("UI 元素树编辑器")
root.geometry("1280x760")
root.minsize(860, 540)

# 全局样式
style = ttk.Style()
try:
    style.theme_use("clam")
except tk.TclError:
    pass

root.configure(bg="#3C3F41")

# ===== PyCharm Darcula 配色 =====
BG_ROOT   = "#3C3F41"   # 工具窗口背景
BG_PANEL  = "#3C3F41"   # 面板/框架
BG_WIDGET = "#2B2B2B"   # 编辑器/树/表格底色
BG_ALT    = "#313335"   # 斑马纹
BG_HEADER = "#2B2B2B"   # 表头
BG_INPUT  = "#4C5052"   # 输入框/控件背景
ACCENT    = "#CC7832"   # PyCharm 橙
SEL_BG    = "#214283"   # Darcula 选中蓝
FG_TEXT   = "#A9B7C6"   # 默认文字
FG_DIM    = "#787878"   # 次要文字
FG_CODE   = "#A9B7C6"   # 代码文字

style.configure("Sash", sashwidth=6, gripcount=0, background=BG_ROOT)

# 通用控件配色（Darcula）
style.configure("TFrame", background=BG_PANEL)
style.configure("TLabel", background=BG_PANEL, foreground=FG_TEXT)
style.configure("TButton", background=BG_INPUT, foreground="#BBB5AF",
                borderwidth=0, focuscolor=ACCENT, padding=(8, 4))
style.map("TButton",
          background=[("active", "#6B6E70"), ("pressed", "#5A5D60")],
          foreground=[("disabled", FG_DIM)])
style.configure("TRadiobutton", background=BG_PANEL, foreground=FG_TEXT)
style.map("TRadiobutton",
          background=[("active", BG_PANEL)],
          foreground=[("active", ACCENT)])
style.configure("TCombobox", fieldbackground=BG_INPUT, background=BG_WIDGET,
                foreground=FG_TEXT, arrowcolor=ACCENT)
style.map("TCombobox",
          fieldbackground=[("readonly", BG_INPUT)],
          foreground=[("readonly", FG_TEXT)])
style.configure("TEntry", fieldbackground=BG_INPUT, foreground=FG_TEXT, insertcolor="#BBB5AF")

# 左侧树 / 右侧表格
style.configure("Treeview",
                rowheight=24,
                fieldbackground=BG_WIDGET,
                background=BG_WIDGET,
                foreground=FG_TEXT,
                borderwidth=0)
style.configure("Treeview.Heading",
                font=("Microsoft YaHei UI", 10, "bold"),
                background=BG_HEADER,
                foreground=ACCENT,
                relief="flat")
style.map("Treeview",
          background=[("selected", SEL_BG)],
          foreground=[("selected", "#ffffff")])

# 左右主分栏
main_paned = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
main_paned.pack(fill="both", expand=True, padx=8, pady=(8, 0))

# --- 左侧：元素层级树 ---
left_frame = ttk.Frame(main_paned, padding=(6, 6, 6, 6))
main_paned.add(left_frame, weight=1)

lbl_tree = ttk.Label(left_frame, text="🗂️ UI 元素层级树（右键操作）",
                     font=("Microsoft YaHei UI", 10, "bold"),
                     foreground=ACCENT)
lbl_tree.pack(anchor="w", pady=(0, 4))

element_tree_outer = ttk.Frame(left_frame)
element_tree_outer.pack(fill="both", expand=True)

# 自定义表头栏：左侧「名称 / ID」，右侧刷新按钮
tree_header = ttk.Frame(element_tree_outer)
tree_header.pack(side="top", fill="x")
ttk.Label(tree_header, text="名称 / ID",
          font=("Microsoft YaHei UI", 10, "bold"),
          foreground=FG_TEXT).pack(side="left", anchor="w")
btn_refresh = ttk.Button(tree_header, text="🔄 刷新", command=reload_tree)
btn_refresh.pack(side="right", anchor="e")

# 元素树下拉，放在刷新按钮左边
combo_frame = ttk.Frame(tree_header)
combo_frame.pack(side="right", padx=(0, 6))
ttk.Label(combo_frame, text="元素树:",
          font=("Microsoft YaHei UI", 9, "bold"), foreground=FG_DIM).pack(side="left", padx=(0, 4))
tree_combo = ttk.Combobox(combo_frame, state="readonly", width=16)
tree_combo.pack(side="left")

element_tree = ttk.Treeview(element_tree_outer, show="tree")
element_tree.column("#0", anchor="w", width=220, stretch=True)

element_tree_sb = ttk.Scrollbar(element_tree_outer, orient="vertical", command=element_tree.yview)
element_tree.configure(yscrollcommand=element_tree_sb.set)
element_tree_sb.pack(side="right", fill="y")
element_tree.pack(side="left", fill="both", expand=True)

# 右键菜单
tree_menu = tk.Menu(root, tearoff=0)
tree_menu.add_command(label="复制组件 ID", command=copy_component_id)
tree_menu.add_command(label="添加组件", command=add_component)
tree_menu.add_separator()
tree_menu.add_command(label="删除组件", command=delete_component)
element_tree.bind("<Button-3>", show_tree_menu)

# --- 右侧：详细内容展示区 ---
right_frame = ttk.Frame(main_paned, padding=(6, 6, 6, 6))
main_paned.add(right_frame, weight=2)

# 顶部工具栏
top_bar = ttk.Frame(right_frame)
top_bar.pack(fill="x", pady=(0, 8))

info_text = tk.StringVar(value="请在左侧选择一个节点")
lbl_info = ttk.Label(top_bar, textvariable=info_text,
                     font=("Microsoft YaHei UI", 10, "bold"),
                     foreground=ACCENT)
lbl_info.pack(side="left", anchor="w")

# 右侧控制区（竖排两行）
right_controls = ttk.Frame(top_bar)
right_controls.pack(side="right")

# 第一行：保存按钮
row1 = ttk.Frame(right_controls)
row1.pack(anchor="e")
btn_save = ttk.Button(row1, text="💾 保存", command=save_to_file)
btn_save.pack(side="left")

# 第二行：定位方式（在保存按钮下方）
radio_frame = ttk.Frame(right_controls)
radio_frame.pack(anchor="e", pady=(2, 0))
ttk.Label(radio_frame, text="定位方式:",
          font=("Microsoft YaHei UI", 9, "bold"), foreground=FG_DIM).pack(side="left", padx=(0, 4))
mode_var = tk.StringVar(value="location")
r_location = ttk.Radiobutton(radio_frame, text="location", value="location",
                             variable=mode_var, command=on_mode_change)
r_location.pack(side="left", padx=3)
r_xpath = ttk.Radiobutton(radio_frame, text="xpath", value="xpath",
                          variable=mode_var, command=on_mode_change)
r_xpath.pack(side="left", padx=3)
r_image = ttk.Radiobutton(radio_frame, text="image", value="image",
                          variable=mode_var, command=on_mode_change)
r_image.pack(side="left", padx=3)

# 右侧内部上下分栏
right_paned = ttk.Panedwindow(right_frame, orient=tk.VERTICAL)
right_paned.pack(fill="both", expand=True)

# 3.1 上方：Excel 风格属性表
top_info_frame = ttk.Frame(right_paned)
right_paned.add(top_info_frame, weight=3)

table_title = tk.StringVar(value="📋 组件属性表 (Excel 风格)")
lbl_attr = ttk.Label(top_info_frame, textvariable=table_title,
                     font=("Microsoft YaHei UI", 9, "bold"),
                     foreground=ACCENT)
lbl_attr.pack(anchor="w", pady=(0, 4))

table_outer = ttk.Frame(top_info_frame)
table_outer.pack(fill="both", expand=True)

prop_table = ttk.Treeview(table_outer,
                          columns=("attr", "value"),
                          show="headings",
                          style="Treeview")
prop_table.heading("attr", text="属性", anchor="w")
prop_table.heading("value", text="值", anchor="w")
prop_table.column("attr", anchor="w", width=180, stretch=False)
prop_table.column("value", anchor="w", width=380, stretch=True)

prop_table.tag_configure("evenrow", background=BG_WIDGET)
prop_table.tag_configure("oddrow", background=BG_ALT)

table_sb = ttk.Scrollbar(table_outer, orient="vertical", command=prop_table.yview)
prop_table.configure(yscrollcommand=table_sb.set)
table_sb.pack(side="right", fill="y")
prop_table.pack(side="left", fill="both", expand=True)

# 双击编辑
prop_table.bind("<Double-1>", on_prop_double_click)

# 3.2 下方：Python 代码块
bottom_code_frame = ttk.Frame(right_paned)
right_paned.add(bottom_code_frame, weight=2)

lbl_code = ttk.Label(bottom_code_frame, text="🐍 do_action (Python 代码块):",
                     font=("Microsoft YaHei UI", 9, "bold"),
                     foreground=ACCENT)
lbl_code.pack(anchor="w", pady=(6, 2))

code_box = tk.Text(bottom_code_frame,
                   font=("Consolas", 10),
                   bg=BG_WIDGET, fg=FG_CODE,
                   relief="solid", borderwidth=1,
                   insertbackground="#BBB5AF",
                   selectbackground=SEL_BG, selectforeground="#ffffff",
                   wrap="word")
code_box.pack(fill="both", expand=True)

# 底部状态栏
status_var = tk.StringVar(value="就绪")
status_bar = ttk.Label(root, textvariable=status_var,
                       font=("Microsoft YaHei UI", 9),
                       background=BG_HEADER, foreground=ACCENT, anchor="w")
status_bar.pack(fill="x", padx=8, pady=(0, 4))

# 初始化：填充元素树下拉并加载默认模块
available_modules = list_data_modules()
tree_combo["values"] = available_modules
if DEFAULT_MODULE in available_modules:
    tree_combo.set(DEFAULT_MODULE)
elif available_modules:
    tree_combo.set(available_modules[0])
tree_combo.bind("<<ComboboxSelected>>", on_combo_select)
if available_modules:
    load_data_module(tree_combo.get())

# 事件绑定
element_tree.bind("<<TreeviewSelect>>", on_tree_select)

root.mainloop()
