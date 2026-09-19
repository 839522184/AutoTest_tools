import re
import subprocess
import time
import tkinter as tk
from tkinter import ttk

# 创建主窗口
root = tk.Tk()
root.title("UI 元素树")
root.geometry("1000x650")

# 创建左右主分栏
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

root.mainloop()