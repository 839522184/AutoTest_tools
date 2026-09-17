# !/usr/bin/python
# -*-coding:utf-8 -*-


# mi14组件树
mi14 = {
    "927c1d36ca92400b8a1f89630ff72929": {
        "name": "设置",
        "do_action": 'start_app(package_name="com.android.settings", activity_name="com.android.settings.Settings")',
        "location": {},
        "container": {},

        "67cfe1e952ca4e338d03f91f9c66ff50": {
            "name": "关于平板电脑",
            "do_action": "",
            "location": {"resourceId": "android:id/title", "text": "关于平板电脑"},
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