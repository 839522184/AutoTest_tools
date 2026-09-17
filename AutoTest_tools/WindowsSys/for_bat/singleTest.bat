@setlocal enabledelayedexpansion
@echo off
echo get the deviceName is %1 port is %2
set port=%2
set udid=%1
echo AppCrawler Pressure test！
for /f "eol=# skip=1 tokens=1,2 delims==" %%i in (conf.properties) do (
	set /a time=%%j-1
	set "package=%%i"
	for /l %%n in (0,1,!time!) do (
	    echo begin round %%n test！
		echo result is !package! %%n
		set "confs=!package!"
		echo !confs!
		if "!confs!"=="settings" (
		set yml= row_settings
		)ELSE if "!confs!"=="launchers" (
		   echo 暂未提供该配置文件
		)ELSE if "!confs!"=="browser" (
		   echo 暂未提供该配置文件
		)ELSE if "!confs!"=="contacts" (
		   echo 暂未提供该配置文件
		)ELSE if "!confs!"=="calculator" (
		   set yml= row_calculator
		)ELSE if "!confs!"=="calendar" (
		   set yml= row_calendar
		)ELSE if "!confs!"=="camera" (
		   set yml= row_camera
		)ELSE if "!confs!"=="clock" (
		   set yml= row_clock
		)ELSE if "!confs!"=="filemanager" (
		   set yml= row_filemanager
		)ELSE if "!confs!"=="gallery" (
		   set yml= row_gallery
		)ELSE if "!confs!"=="recorder" (
		   set yml= row_recorder
		)
		echo !yml!
		echo disable flymode
		adb -s !udid! shell settings put global airplane_mode_on 0
		echo enable wifi
		adb -s !udid! shell svc wifi enable
		echo Go Launcher
		adb -s !udid! shell am start -n com.zui.launcher/com.zui.launcher.drawer.DrawerLauncher
		if "!confs!"=="settings" (
			echo java -javaagent:appcrawler-2.7.4-hogwarts-row-encryp.jar -jar appcrawler-2.7.4-hogwarts-row-encryp.jar -s !yml! --capability udid=!udid! --appium !port!
			java -javaagent:appcrawler-2.7.4-hogwarts-row-encryp.jar -jar appcrawler-2.7.4-hogwarts-row-encryp.jar -s !yml! --capability udid=!udid! --appium !port!
			echo enable wifi
			adb -s !udid! shell settings put global airplane_mode_on 0
			adb -s !udid! shell svc wifi enable
		) ELSE (
			echo java -javaagent:appcrawler-2.7.4-hogwarts-encryp.jar -jar appcrawler-2.7.4-hogwarts-encryp.jar -s !yml! --capability udid=!udid! --appium !port!
			java -javaagent:appcrawler-2.7.4-hogwarts-encryp.jar -jar appcrawler-2.7.4-hogwarts-encryp.jar -s !yml! --capability udid=!udid! --appium !port!
		)
		)
)