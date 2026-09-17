::自动获取已连接设备，并发起AppCrawler的单应用压力测试，多设备多应用测试需Debug！
@setlocal enabledelayedexpansion
@echo off
echo start AppCrawler test!
set tmpDevSN=HA1X75D8
set port=4723
start cmd /k call singleTest.bat !tmpDevSN! !port!
