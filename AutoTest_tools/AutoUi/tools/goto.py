# from UiLocations import location_tree
#
#
# """
# UI界面全局导航
# """
#
#
# def location_init(location_path):
#     """
#     goto前，location初始化操作
#     :param location_path:
#     :return:
#     """
#     run_list = []
#     # 拆分路径，用于提取元素定位信息
#     location_names = location_path.split("/")
#     for name_index, action_name in enumerate(location_names):
#         # 当前操作的元素信息
#         action_dict = location_tree.get(action_name)
#         run_list.append(action_dict)
#     return run_list
#
#
# def get_element_path(target_key):
#     """
#     依据唯一ID逆推嵌套路径
#     :param target_key:
#     :return:
#     """
#
#     def traverse(d, path):
#         if isinstance(d, dict):
#             for key, value in d.items():
#                 new_path = path + [key]
#                 if key == target_key:
#                     return new_path
#                 result = traverse(value, new_path)
#                 if result:
#                     return result
#         elif isinstance(d, list):
#             for index, item in enumerate(d):
#                 new_path = path + [index]
#                 result = traverse(item, new_path)
#                 if result:
#                     return result
#         return None
#
#     return traverse(location_tree, [])
#
#
# def run_action(action):
#     """
#     执行导航过程中穿插的操作
#     :param action:
#     :return:
#     """
#
# 
#
#
#
# def run_find_element_for_container(parent_element, **selector):
#     """
#     在指定元素范围内查找元素，支持滑动查找
#     :param parent_element: 父元素对象
#     :param selector: 查找元素的选择器，例如 text='目标文本', resourceId='com.example:id/button'
#     :return: 找到的元素对象，如果未找到则返回 None
#     """
#     try:
#         # 获取父元素的边界信息
#         parent_bounds = parent_element.info.get('bounds')
#         if not parent_bounds:
#             print("无法获取父元素的边界信息")
#             return None
#
#         def check_elements():
#             # 获取屏幕上所有符合选择器的元素
#             all_elements = parent_element.siblings(**selector) + parent_element.child(**selector)
#             assert all_elements, "容器下没有找到指定组件，请检查容器与组件关系"
#             # 筛选出在父元素范围内的元素
#             for element in all_elements:
#                 element_bounds = element.info.get('bounds')
#                 if element_bounds:
#                     if (element_bounds['left'] >= parent_bounds['left'] and
#                             element_bounds['right'] <= parent_bounds['right'] and
#                             element_bounds['top'] >= parent_bounds['top'] and
#                             element_bounds['bottom'] <= parent_bounds['bottom']):
#                         return element
#             return None
#
#         # 先向上滑动查找
#         last_bounds = parent_element.info['bounds']
#         while True:
#             result = check_elements()
#             if result:
#                 return result
#             parent_element.swipe("up")
#             current_bounds = parent_element.info['bounds']
#             if current_bounds == last_bounds:
#                 break
#             last_bounds = current_bounds
#
#         # 若向上未找到，向下滑动查找
#         last_bounds = parent_element.info['bounds']
#         while True:
#             result = check_elements()
#             if result:
#                 return result
#             parent_element.swipe("down")
#             current_bounds = parent_element.info['bounds']
#             if current_bounds == last_bounds:
#                 break
#             last_bounds = current_bounds
#
#         return None
#     except Exception as e:
#         print(f"查找元素时出现错误: {e}")
#         return None
#
#
# def goto(l_id, location_path):
#     """
#     :param l_id: 唯一ID
#     :param location_path: "我的设备/全部参数与信息/xxx"，主要起到标注作用
#     :return: 定位到的元素
#     """
#     run_list = get_element_path(l_id)
#
#     # 遍历执行每一步操作，实现导航
#     for name_index, uid in enumerate(run_list):
#         # 当前操作的元素信息
#         action_dict = location_tree.get(uid).get("do_action")
#         location_dict = location_tree.get(uid).get("location")
#         container = action_dict.get(uid).get("container")
#
#         action = action_dict["action"]
#         if action:
#             # 执行前操作
#             run_action(action=action)
#         if container:
#             # 执行从容器查找元素操作
#             print(f"从容器{container}内查找 {location_dict}")
#             parent_element =
#             run_find_element_for_container()
#
#         # 找到元素后的操作
#         if name_index == len(run_list):
#             element = ""
#             # 最后返回定位到的页面元素
#             return element
#         else:
#             # 非最后一个元素，主动执行点击操作
#             element = ""
#             # element.click()
