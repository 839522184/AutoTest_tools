import os
import sys
import site
import tempfile
import time
import datetime
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# 本机 Python3.8 的 ENABLE_USER_SITE=False（user site 默认不加载），
# 手动把 user site 目录加入搜索路径，以加载 pip --user 安装的 Pillow 等包。
try:
    site.addsitedir(site.USER_SITE)
except Exception:
    pass

from PIL import Image, ImageTk

# 把项目根目录（element_tree/ 的父目录）加入 sys.path，
# 保证无论从哪个工作目录启动（python tree.py / python -m element_tree.tree / 双击），
# 都能以包方式 import element_tree 下的子模块。
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from element_tree.get_uuid import generate_unique_id

# 存储节点 iid -> (key, value) 映射
node_data_map = {}


def _log(msg):
    """打印操作日志到 PyCharm 控制台，带毫秒级时间戳。"""
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}", flush=True)


# 是否有未保存的修改：置位时保存按钮高亮
_dirty = False


def _set_dirty(dirty):
    """切换「未保存」状态，并同步保存按钮的高亮样式。"""
    global _dirty
    if dirty == _dirty:
        return
    _dirty = dirty
    if dirty:
        btn_save.config(style="SaveDirty.TButton", text="💾 保存*")
    else:
        btn_save.config(style="TButton", text="💾 保存")


# ------------------------ ** 变量在此处存放 **
# 元素树数据所在包与目录
DATA_PACKAGE = "element_tree.element_tree_data"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "element_tree_data")
SAVE_HEADER = "# 本文件由 tree.py 自动生成/覆盖保存\n"
DEFAULT_MODULE = "Demo_data"   # 默认加载的元素树模块名

# 图片相关
IMAGE_DIR = os.path.join(_PROJECT_ROOT, "element_tree", "Images")  # 裁剪图片保存目录
IMAGE_PREVIEW_WIDTH = 300      # 缩略图最大宽度（px）
IMAGE_REL_PREFIX = "element_tree/Images"   # 落盘时写入 image_path 的相对路径前缀
ADB_EXEC = "adb"               # adb 可执行文件（已在 PATH 或填完整路径）
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
    return current_node


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
    _set_dirty(False)  # 切换元素树后未保存状态清零
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
        table_title.set(f"📋 组件属性表 — 按 location_flag={current_mode} 展示（双击值可编辑）")
    else:
        prop_table.insert("", "end", values=("（分类节点）", "无定位与容器属性"), tags=("evenrow",))
        table_title.set("📋 组件属性表")

    # 4. 下方 do_action 代码块
    code_box.delete("1.0", tk.END)
    if is_dict and val.get("do_action"):
        code_box.insert(tk.END, val["do_action"])
    else:
        code_box.insert(tk.END, "# 该节点没有关联的 Python 代码")

    # 5. 刷新右上图片预览区（image 定位方式下展示缩略图 / 框选）
    _refresh_image_preview(is_dict, current_mode)


def commit_edit(attr, new_text):
    """把表格里编辑后的值写回底层 data 字典（仅改内存，保存需点「保存」按钮）。
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

    _log(f"修改组件 [{key}] 属性 {attr}: {old_val!r} -> {new_text!r}（未保存）")

    update_right_display(from_tree_click=False)
    status_var.set(f"✏️ 已更新 {attr}（未保存，点击「保存」落盘）")
    _set_dirty(True)


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
    status_var.set(f"➕ 已添加组件: {name}（未保存，点击「保存」落盘）")
    _set_dirty(True)


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
    _log(f"删除组件: ID={key}, 名称={name!r}（未保存）")
    status_var.set(f"🗑️ 已删除组件: {name}（未保存，点击「保存」落盘）")
    _set_dirty(True)


def add_component_ocr():
    """右键「新增-OCR」：Android 截图 → 弹窗框选 → RapidOCR 识别 → 以识别内容新建组件。"""
    sel = element_tree.selection()
    if not sel:
        messagebox.showinfo("提示", "请先在左侧选中一个父节点", parent=root)
        return
    parent_iid = sel[0]
    pkey, pval = node_data_map[parent_iid]
    if not isinstance(pval, dict):
        messagebox.showwarning("无法添加", "该节点不是容器，无法添加子组件", parent=root)
        return

    # 1. Android 截图
    tmp = os.path.join(tempfile.gettempdir(),
                       f"adb_shot_ocr_{datetime.datetime.now().strftime('%H%M%S%f')}.png")
    ok, msg = take_android_screenshot(tmp)
    if not ok:
        messagebox.showerror("截图失败", msg, parent=root)
        return
    try:
        img = Image.open(tmp).convert("RGB")
    except Exception as e:
        messagebox.showerror("截图读取失败", str(e), parent=root)
        return

    # 2. 弹窗展示截图，供框选 + OCR
    win = tk.Toplevel(root)
    win.title("新增组件 - OCR 框选识别")
    win.configure(bg=BG_PANEL)
    win.transient(root)
    win.grab_set()

    max_w, max_h = 900, 540
    scale = min(max_w / img.width, max_h / img.height, 1.0)
    disp_w, disp_h = max(1, int(img.width * scale)), max(1, int(img.height * scale))
    photo = ImageTk.PhotoImage(img.resize((disp_w, disp_h)))
    win._photo = photo

    canvas = tk.Canvas(win, width=disp_w, height=disp_h, bg=BG_WIDGET,
                       highlightthickness=0, cursor="crosshair")
    canvas.pack(padx=8, pady=(8, 0))
    canvas.create_image(0, 0, anchor="nw", image=photo)

    state = {"start": None, "rect": None, "name": ""}
    result_var = tk.StringVar(value="拖动鼠标框选目标区域后点击 OCR")

    def reset_ocr_state():
        btn_ocr.config(text="📖 OCR", state="normal", command=do_ocr)
        result_var.set("拖动鼠标框选目标区域后点击 OCR")

    def on_press(e):
        state["start"] = (e.x, e.y)
        if state["rect"]:
            canvas.delete(state["rect"])
            state["rect"] = None
        state["name"] = ""
        reset_ocr_state()

    def on_drag(e):
        if state["start"] is None:
            return
        if state["rect"]:
            canvas.delete(state["rect"])
        x0, y0 = state["start"]
        state["rect"] = canvas.create_rectangle(x0, y0, e.x, e.y,
                                                outline=ACCENT, width=2)

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)

    # 3. 底部按钮区：识别结果(左) + 取消 / OCR(确定)（右）
    bar = ttk.Frame(win)
    bar.pack(fill="x", pady=8)
    result_lbl = ttk.Label(bar, textvariable=result_var, foreground=ACCENT)
    result_lbl.pack(side="left", padx=12)

    def do_ocr():
        if not state["rect"]:
            messagebox.showwarning("未框选", "请先拖动鼠标框选目标区域", parent=win)
            return
        x0, y0, x2, y2 = canvas.coords(state["rect"])
        left, top = int(min(x0, x2) / scale), int(min(y0, y2) / scale)
        right, bot = int(max(x0, x2) / scale), int(max(y0, y2) / scale)
        if right - left < 2 or bot - top < 2:
            messagebox.showwarning("区域过小", "框选区域过小，请重新框选", parent=win)
            return
        crop = img.crop((left, top, right, bot))
        btn_ocr.config(text="⏳ 识别中...", state="disabled")
        result_var.set("正在用 RapidOCR 识别...")

        def work():
            info = ocr(crop)
            root.after(0, lambda: on_ocr_done(info))

        threading.Thread(target=work, daemon=True).start()

    def on_ocr_done(info):
        btn_ocr.config(state="normal")
        texts = info["str_list"]
        if not texts:
            result_var.set("未识别到文字，请重新框选后再试")
            btn_ocr.config(text="📖 OCR", command=do_ocr)
            return
        state["name"] = texts[0]
        result_var.set(f"识别结果: {texts[0]}（点击确定新建组件）")
        btn_ocr.config(text="✅ 确定", command=do_confirm)

    def do_confirm():
        name = state.get("name", "").strip()
        if not name:
            messagebox.showwarning("无识别结果", "请先框选并点击 OCR 识别出组件名", parent=win)
            return
        try:
            # 1) 用当前框选区域裁剪图片，保存到 Images 目录
            if state["rect"]:
                x0, y0, x2, y2 = canvas.coords(state["rect"])
                left, top = int(min(x0, x2) / scale), int(min(y0, y2) / scale)
                right, bot = int(max(x0, x2) / scale), int(max(y0, y2) / scale)
            else:
                left, top, right, bot = 0, 0, img.width, img.height
            os.makedirs(IMAGE_DIR, exist_ok=True)
            fname = f"{_safe_filename(name)}_{datetime.datetime.now().strftime('%H%M%S')}.png"
            img.crop((left, top, right, bot)).save(os.path.join(IMAGE_DIR, fname), "PNG")
            rel_path = f"{IMAGE_REL_PREFIX}/{fname}"

            # 2) 组装新组件：识别结果同时作为 name / location.text / xpath
            xpath_attr = f'//*[@text="{name.replace(chr(34), chr(39))}"]'
            new_id = generate_unique_id()
            new_node = {
                "name": name,
                "do_action": "",
                "location_flag": "location",
                "location": {"resourceId": "", "text": name, "description": ""},
                "xpath": xpath_attr,
                "image": {"image_path": rel_path, "compare": 0.85},
                "container": {"xpath": "//*[]"},
            }
            pval[new_id] = new_node
            child_iid = element_tree.insert(parent_iid, "end", text=f"{name} ({new_id})")
            node_data_map[child_iid] = (new_id, new_node)
            element_tree.item(parent_iid, open=True)
            element_tree.selection_set(child_iid)
            update_right_display(from_tree_click=True)
            status_var.set(f"➕ OCR 新增组件: {name}（未保存，点击「保存」落盘）")
            _log(f"OCR 新增组件: 父节点={pkey}, 新组件 ID={new_id}, 名称={name!r}, "
                 f"image={rel_path}, xpath={xpath_attr}（未保存）")
            _set_dirty(True)
        finally:
            win.grab_release()
            win.destroy()

    btn_cancel = ttk.Button(bar, text="取消", command=win.destroy)
    btn_cancel.pack(side="right", padx=(4, 12))
    btn_ocr = ttk.Button(bar, text="📖 OCR", command=do_ocr)
    btn_ocr.pack(side="right")


def show_tree_menu(event):
    iid = element_tree.identify_row(event.y)
    if iid:
        element_tree.selection_set(iid)
        element_tree.focus(iid)
    tree_menu.tk_popup(event.x_root, event.y_root)


# ============ 左侧树拖拽改层级 ============

# 拖拽状态
_drag = {"item": None, "x": 0, "y": 0, "moving": False}
_drag_ghost = None   # 拖拽时的悬浮跟随窗口


def _is_ancestor(anc, node):
    """判断 anc 是否为 node 的祖先节点（含自身）。"""
    p = node
    while p:
        if p == anc:
            return True
        p = element_tree.parent(p)
    return False


def _rebuild_tree():
    """按当前 data 重建左侧树（不重置未保存状态）。"""
    element_tree.delete(*element_tree.get_children())
    node_data_map.clear()
    for k, v in data.items():
        insert_node(element_tree, "", k, v)
    expand_all(element_tree)


def _find_iid_by_key(key, parent=""):
    """在树中按存储 key 递归查找节点 iid，找不到返回 None。"""
    for child in element_tree.get_children(parent):
        ckey, _ = node_data_map.get(child, (None, None))
        if ckey == key:
            return child
        found = _find_iid_by_key(key, child)
        if found:
            return found
    return None


def _move_node(src_iid, target_iid):
    """把 src_iid 节点移动到 target_iid（作为其子节点）；target_iid 为空则移到顶层。"""
    if src_iid == target_iid:
        return
    if target_iid and _is_ancestor(src_iid, target_iid):
        messagebox.showwarning("无法移动", "不能把节点移动到其自身或其子节点下", parent=root)
        return

    skey, sval = node_data_map.get(src_iid, (None, None))
    if skey is None:
        return

    # 先校验目标是否为可作父的容器（dict）
    if target_iid:
        tkey, tval = node_data_map.get(target_iid, (None, None))
        if not isinstance(tval, dict):
            messagebox.showwarning("无法移动", "目标节点不是容器，无法作为父节点", parent=root)
            return

    # 从源父字典中摘除
    src_parent = element_tree.parent(src_iid)
    if src_parent:
        _, spval = node_data_map.get(src_parent, (None, None))
        if isinstance(spval, dict) and skey in spval:
            del spval[skey]
        else:
            return
    else:
        if skey in data:
            del data[skey]
        else:
            return

    # 挂到目标下
    if target_iid:
        tkey, tval = node_data_map.get(target_iid, (None, None))
        tval[skey] = sval
        _log(f"拖拽移动: {skey}（{sval.get('name', skey)}）-> 挂到 {tkey}（{tval.get('name', tkey)}）下（未保存）")
    else:
        data[skey] = sval
        _log(f"拖拽移动: {skey}（{sval.get('name', skey)}）-> 顶层（未保存）")

    # 重建树并选中移动后的节点
    _rebuild_tree()
    new_iid = _find_iid_by_key(skey)
    if new_iid:
        element_tree.selection_set(new_iid)
        element_tree.focus(new_iid)
        parent_iid = element_tree.parent(new_iid)
        if parent_iid:
            element_tree.item(parent_iid, open=True)
    update_right_display(from_tree_click=True)
    status_var.set("↕️ 已移动组件层级（未保存，点击「保存」落盘）")
    _set_dirty(True)


def _iter_all_items(root_item=""):
    """递归收集树上全部节点 iid。"""
    items = list(element_tree.get_children(root_item))
    for it in items:
        items.extend(_iter_all_items(it))
    return items


def _clear_drop_tags():
    """清除所有行上的落点高亮 tag。"""
    for it in _iter_all_items():
        tags = list(element_tree.item(it, "tags") or ())
        if "drop" in tags or "drop_bad" in tags:
            element_tree.item(it, tags=[t for t in tags if t not in ("drop", "drop_bad")])


def _is_drop_valid(target_iid, src_iid):
    """判断 target 能否作为 src 的新父。返回 (是否可放, 落点描述)。"""
    if not target_iid:
        return True, "顶层"
    if target_iid == src_iid:
        return False, "不能拖到自身"
    if _is_ancestor(src_iid, target_iid):
        return False, "不能拖到自己的子节点"
    tkey, tval = node_data_map.get(target_iid, (None, None))
    if not isinstance(tval, dict):
        return False, "目标不是容器"
    return True, f"{tval.get('name', tkey)} 下"


def _update_ghost(event, src_text):
    """创建或移动悬浮跟随窗口（无边框置顶，显示被拖节点文本）。"""
    global _drag_ghost
    if _drag_ghost is None:
        _drag_ghost = tk.Toplevel(root)
        _drag_ghost.overrideredirect(True)
        _drag_ghost.attributes("-topmost", True)
        lbl = tk.Label(_drag_ghost, bg="#2b2b2b", fg="#ffffff",
                       relief="solid", borderwidth=1, padx=6, pady=2,
                       font=("Microsoft YaHei UI", 9))
        lbl.pack()
        _drag_ghost._lbl = lbl
    _drag_ghost.geometry(f"+{event.x_root + 16}+{event.y_root + 12}")


def _update_drop_preview(event):
    """位置预知：根据鼠标所在行判定落点，高亮目标并更新悬浮窗文字。"""
    if _drag_ghost is None:
        return
    target = element_tree.identify_row(event.y)
    ok, reason = _is_drop_valid(target, _drag["item"])
    _clear_drop_tags()
    if ok and target:
        element_tree.item(target, tags=("drop",))
    elif target:
        element_tree.item(target, tags=("drop_bad",))

    src_text = element_tree.item(_drag["item"], "text")
    if ok:
        _drag_ghost._lbl.config(text=f"⇣ {src_text} 将移动到: {reason}")
    else:
        _drag_ghost._lbl.config(text=f"✖ {reason}（{src_text}）")


def _on_tree_press(event):
    _drag["item"] = element_tree.identify_row(event.y)
    _drag["x"] = event.x
    _drag["y"] = event.y
    _drag["moving"] = False


def _on_tree_drag(event):
    if not _drag["item"]:
        return
    dx = abs(event.x - _drag["x"])
    dy = abs(event.y - _drag["y"])
    if not _drag["moving"] and (dx > 8 or dy > 8):
        _drag["moving"] = True
    if _drag["moving"]:
        src_text = element_tree.item(_drag["item"], "text")
        _update_ghost(event, src_text)
        _update_drop_preview(event)


def _on_tree_release(event):
    global _drag_ghost
    src = _drag["item"]
    was_moving = _drag["moving"]
    _drag["item"] = None
    _drag["moving"] = False
    element_tree.configure(cursor="")
    _clear_drop_tags()
    if _drag_ghost is not None:
        _drag_ghost.destroy()
        _drag_ghost = None
    if not src or not was_moving:
        return
    target = element_tree.identify_row(event.y)
    _move_node(src, target)


# ============ 图片预览 / Android 截图 / 框选 ============

# 持有当前缩略图引用，防止被 GC 回收
_preview_photo = None


def _resolve_image_path(path):
    """把 image_path（相对项目根或绝对路径）解析成绝对路径；不存在则返回 None。"""
    if not path:
        return None
    if os.path.isabs(path):
        return path if os.path.exists(path) else None
    abs_p = os.path.join(_PROJECT_ROOT, path)
    return abs_p if os.path.exists(abs_p) else None


def take_android_screenshot(dest_path):
    """用 adb 从 Android 设备截屏保存到 dest_path。返回 (ok, msg)。"""
    try:
        result = subprocess.run([ADB_EXEC, "exec-out", "screencap", "-p"],
                                capture_output=True, timeout=20)
    except FileNotFoundError:
        return False, f"未找到 adb（{ADB_EXEC}），请确认已安装并加入 PATH"
    except Exception as e:
        return False, f"adb 调用失败: {e}"
    if result.returncode != 0:
        return False, result.stderr.decode("utf-8", "ignore").strip() or "adb 截图失败（请确认已连接设备）"
    if not result.stdout:
        return False, "adb 返回空数据，截图失败"
    with open(dest_path, "wb") as f:
        f.write(result.stdout)
    return True, dest_path

# RapidOCR 引擎（懒加载 + 线程锁，避免重复初始化模型）
_ocr_engine = None
_ocr_lock = threading.Lock()


def ocr(img, use_cls=True, use_rec=True):
    """使用 RapidOCR 识别图片，返回识别信息字典。

    参数:
        img: PIL Image / numpy.ndarray（BGR）/ 文件路径 / bytes，均可识别
        use_cls: 是否启用方向分类（默认开启，提高竖排/旋转文字识别率）
        use_rec: 是否启用文本识别（默认开启）

    返回:
        {"str_list": [...每行文本...], "strings": "拼接全部文本", "lines": 行数}
        识别失败或无可识别文字时返回全空结构。
    """
    import numpy as np
    global _ocr_engine
    try:
        # 懒加载引擎：首次调用时初始化，之后复用（RapidOCR 模型加载耗时约几秒）
        if _ocr_engine is None:
            with _ocr_lock:
                if _ocr_engine is None:
                    from rapidocr_onnxruntime import RapidOCR
                    _ocr_engine = RapidOCR()

        # 统一转成 RapidOCR 接受的输入：PIL/RGB ndarray -> BGR ndarray
        if hasattr(img, "convert"):                      # PIL Image
            arr = np.array(img.convert("RGB"))[:, :, ::-1].copy()
        elif hasattr(img, "shape"):                       # 已是 ndarray
            arr = img
        else:                                             # 路径 / bytes
            arr = img

        start = time.time()
        result, _ = _ocr_engine(arr, use_cls=use_cls, use_rec=use_rec)
        _log(f"OCR 识别完成，耗时 {time.time() - start:.3f}s")
    except Exception as e:
        _log(f"OCR 识别失败: {e}")
        return {"str_list": [], "strings": "", "lines": 0}

    str_list = []
    strings = ""
    if result:
        for res in result:
            if len(res) >= 2 and res[1]:
                text = str(res[1]).strip()
                str_list.append(text)
                strings += text
    return {"str_list": str_list, "strings": strings, "lines": len(str_list)}

def show_full_image(abs_path):
    """弹窗展示原图（可滚动查看）。"""
    win = tk.Toplevel(root)
    win.title("原图预览")
    win.configure(bg=BG_PANEL)
    try:
        img = Image.open(abs_path).convert("RGB")
    except Exception as e:
        messagebox.showerror("预览失败", f"无法打开图片: {e}", parent=root)
        win.destroy()
        return
    photo = ImageTk.PhotoImage(img)
    win._photo = photo  # 持有引用防 GC
    canvas = tk.Canvas(win, bg=BG_WIDGET, highlightthickness=0)
    hs = ttk.Scrollbar(win, orient="horizontal", command=canvas.xview)
    vs = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
    canvas.configure(xscrollcommand=hs.set, yscrollcommand=vs.set)
    canvas.create_image(0, 0, anchor="nw", image=photo)
    canvas.config(scrollregion=(0, 0, img.width, img.height))
    canvas.grid(row=0, column=0, sticky="nsew")
    vs.grid(row=0, column=1, sticky="ns")
    hs.grid(row=1, column=0, sticky="ew")
    win.rowconfigure(0, weight=1)
    win.columnconfigure(0, weight=1)
    win.geometry("900x650")


def _safe_filename(name):
    """把名称清洗成可用作文件名的字符串。"""
    cleaned = "".join(c for c in str(name) if c.isalnum() or c in "-_.").strip(" .")
    return cleaned or "img"


def _refresh_image_preview(is_dict, mode):
    """按当前选中节点刷新「缩略图展示区」：image 定位方式下展示缩略图 + 框选按钮。"""
    global _preview_photo
    for w in image_preview_body.winfo_children():
        w.destroy()

    # 仅 image 定位方式下展示
    if not (is_dict and mode == "image"):
        ttk.Label(image_preview_body, text="📷 仅 image 定位方式下展示缩略图",
                  foreground=FG_DIM).pack(anchor="w")
        return

    sel = element_tree.selection()
    if not sel:
        ttk.Label(image_preview_body, text="请在左侧选择一个组件节点",
                  foreground=FG_DIM).pack(anchor="w")
        return
    key, val = node_data_map.get(sel[0], (None, None))
    img_path = ""
    if isinstance(val, dict):
        img = val.get("image", {})
        img_path = img.get("image_path", "") if isinstance(img, dict) else ""
    abs_path = _resolve_image_path(img_path)

    if not abs_path:
        ttk.Label(image_preview_body, text="⚠️ 未找到图片文件，可用「框选」从 Android 截图生成",
                  foreground=ACCENT).pack(anchor="w")
        ttk.Button(image_preview_body, text="📌 框选", command=lambda: box_select_image(key, val)).pack(anchor="w", pady=(4, 0))
        return

    try:
        img = Image.open(abs_path)
        img.thumbnail((IMAGE_PREVIEW_WIDTH, 300))
        _preview_photo = ImageTk.PhotoImage(img)
    except Exception as e:
        ttk.Label(image_preview_body, text=f"⚠️ 图片加载失败: {e}", foreground=ACCENT).pack(anchor="w")
        ttk.Button(image_preview_body, text="📌 框选", command=lambda: box_select_image(key, val)).pack(anchor="w", pady=(4, 0))
        return

    # image.image_path 信息行 + 框选按钮：放在缩略图上方，避免缩略图过大挡住按钮
    path_row = ttk.Frame(image_preview_body)
    path_row.pack(fill="x", pady=(0, 6), anchor="w")
    ttk.Label(path_row, text=f"image.image_path: {img_path}",
              foreground=FG_TEXT).pack(side="left")
    ttk.Button(path_row, text="📌 框选", command=lambda: box_select_image(key, val)).pack(side="left", padx=(10, 0))

    lbl = ttk.Label(image_preview_body, image=_preview_photo, cursor="hand2")
    lbl.image = _preview_photo
    lbl.pack(anchor="w")
    lbl.bind("<Button-1>", lambda e: show_full_image(abs_path))
    ttk.Label(image_preview_body, text="🖱️ 点击缩略图查看原图",
              foreground=FG_DIM).pack(anchor="w")


def box_select_image(key, val):
    """Android 截图并弹窗框选，保存裁剪图片到 IMAGE_DIR，回写 image_path。"""
    tmp = os.path.join(tempfile.gettempdir(), f"adb_shot_{str(key)[:8]}.png")
    ok, msg = take_android_screenshot(tmp)
    if not ok:
        messagebox.showerror("截图失败", msg, parent=root)
        return
    try:
        img = Image.open(tmp).convert("RGB")
    except Exception as e:
        messagebox.showerror("截图读取失败", str(e), parent=root)
        return

    win = tk.Toplevel(root)
    win.title(f"框选图片区域 — {val.get('name', key) if isinstance(val, dict) else key}")
    win.configure(bg=BG_PANEL)
    win.transient(root)
    win.grab_set()

    # 缩放展示（原图可能很大）
    max_w, max_h = 900, 540
    scale = min(max_w / img.width, max_h / img.height, 1.0)
    disp_w, disp_h = max(1, int(img.width * scale)), max(1, int(img.height * scale))
    photo = ImageTk.PhotoImage(img.resize((disp_w, disp_h)))
    win._photo = photo

    canvas = tk.Canvas(win, width=disp_w, height=disp_h, bg=BG_WIDGET,
                       highlightthickness=0, cursor="crosshair")
    canvas.pack(padx=8, pady=(8, 0))
    canvas.create_image(0, 0, anchor="nw", image=photo)

    state = {"start": None, "rect": None}

    def on_press(e):
        state["start"] = (e.x, e.y)
        if state["rect"]:
            canvas.delete(state["rect"])
            state["rect"] = None

    def on_drag(e):
        if state["start"] is None:
            return
        if state["rect"]:
            canvas.delete(state["rect"])
        x0, y0 = state["start"]
        state["rect"] = canvas.create_rectangle(
            x0, y0, e.x, e.y, outline=ACCENT, width=2)

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)

    bar = ttk.Frame(win)
    bar.pack(fill="x", pady=8)
    ttk.Label(bar, text="拖动鼠标框选目标区域", foreground=FG_DIM).pack(side="left", padx=12)
    ttk.Button(bar, text="取消", command=win.destroy).pack(side="right", padx=(4, 12))

    def do_save():
        if not state["rect"]:
            messagebox.showwarning("未框选", "请先拖动鼠标框选目标区域", parent=win)
            return
        x0, y0, x2, y2 = canvas.coords(state["rect"])
        left, top = int(min(x0, x2) / scale), int(min(y0, y2) / scale)
        right, bot = int(max(x0, x2) / scale), int(max(y0, y2) / scale)
        if right - left < 2 or bot - top < 2:
            messagebox.showwarning("区域过小", "框选区域过小，请重新框选", parent=win)
            return
        crop = img.crop((left, top, right, bot))
        os.makedirs(IMAGE_DIR, exist_ok=True)
        name_src = val.get("name") if isinstance(val, dict) else key
        fname = f"{_safe_filename(name_src)}_{datetime.datetime.now().strftime('%H%M%S')}.png"
        save_path = os.path.join(IMAGE_DIR, fname)
        crop.save(save_path, "PNG")
        rel_path = f"{IMAGE_REL_PREFIX}/{fname}"
        if isinstance(val, dict):
            val.setdefault("image", {})["image_path"] = rel_path
        status_var.set(f"🖼️ 已保存裁剪图片: {rel_path}（未保存，点击「保存」落盘）")
        _log(f"框选保存图片: {key} -> {rel_path}（未保存）")
        update_right_display(from_tree_click=False)
        _set_dirty(True)
        win.destroy()

    ttk.Button(bar, text="💾 保存", command=do_save).pack(side="right")


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
        _set_dirty(False)  # 保存成功，取消高亮
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
    """手动切换右上定位方式时，把选择写回当前节点的 location_flag（仅内存，保存需点「保存」按钮）。"""
    sel = element_tree.selection()
    if sel:
        key, val = node_data_map.get(sel[0], (None, None))
        if isinstance(val, dict):
            chosen = mode_var.get()
            old_flag = val.get("location_flag", "location")
            if old_flag != chosen:
                val["location_flag"] = chosen
                _log(f"组件 [{val.get('name','?')} ({key})] 定位方式 {old_flag} -> {chosen}（未保存）")
                status_var.set(f"🏷️ 已将定位方式记为 {chosen}（未保存，点击「保存」落盘）")
                _set_dirty(True)
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

# 保存按钮「有未保存修改」时的高亮样式（醒目橙色）
style.configure("SaveDirty.TButton", background=ACCENT, foreground="#1e1e1e",
                borderwidth=0, font=("Microsoft YaHei UI", 9, "bold"),
                padding=(8, 4))
style.map("SaveDirty.TButton",
          background=[("active", "#e09a5a"), ("pressed", "#b9671f")],
          foreground=[("disabled", "#1e1e1e")])

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
# 拖拽落点高亮：合法=橙色，非法=暗红
element_tree.tag_configure("drop", background=ACCENT)
element_tree.tag_configure("drop_bad", background="#8c2f2f")

element_tree_sb = ttk.Scrollbar(element_tree_outer, orient="vertical", command=element_tree.yview)
element_tree.configure(yscrollcommand=element_tree_sb.set)
element_tree_sb.pack(side="right", fill="y")
element_tree.pack(side="left", fill="both", expand=True)

# 右键菜单
tree_menu = tk.Menu(root, tearoff=0)
tree_menu.add_command(label="复制组件 ID", command=copy_component_id)
tree_menu.add_command(label="添加组件", command=add_component)
tree_menu.add_command(label="添加组件-OCR", command=add_component_ocr)
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

# 3.1 属性展示区（weight=2）
top_info_frame = ttk.Frame(right_paned)
right_paned.add(top_info_frame, weight=2)

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

# 3.2 缩略图展示区（weight=3）
image_preview_frame = ttk.Frame(right_paned)
right_paned.add(image_preview_frame, weight=3)
ttk.Label(image_preview_frame, text="🖼️ 图片预览区（点击缩略图查看原图）",
          font=("Microsoft YaHei UI", 9, "bold"),
          foreground=ACCENT).pack(anchor="w", pady=(6, 2))
image_preview_body = ttk.Frame(image_preview_frame)
image_preview_body.pack(fill="both", expand=True)

# 3.3 do_action 展示区（weight=1）
bottom_code_frame = ttk.Frame(right_paned)
right_paned.add(bottom_code_frame, weight=1)

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
# 拖拽改层级
element_tree.bind("<ButtonPress-1>", _on_tree_press)
element_tree.bind("<B1-Motion>", _on_tree_drag)
element_tree.bind("<ButtonRelease-1>", _on_tree_release)


def _init_pane_ratios():
    """初始按 1:1:1 分配右侧三栏（属性:缩略图:do_action）。

    ttk.Panedwindow 的 weight 只在窗口拉伸时生效，初始布局按各 pane 内容
    实际大小分配，导致内容少的缩略图区被压扁。这里在布局完成后手动把两个
    分隔条设到 1/3 与 2/3 的高度位置，强制三栏按 1:1:1 展示。
    """
    try:
        root.update_idletasks()
        h = right_paned.winfo_height()
        if h > 10:
            right_paned.sashpos(0, int(h * 1 / 3))
            right_paned.sashpos(1, int(h * 2 / 3))
    except tk.TclError:
        pass


# 窗口较小/非最大化时布局也较慢，多试几次确保比例生效
root.after(80, _init_pane_ratios)
root.after(300, _init_pane_ratios)
root.after(600, _init_pane_ratios)

root.mainloop()
