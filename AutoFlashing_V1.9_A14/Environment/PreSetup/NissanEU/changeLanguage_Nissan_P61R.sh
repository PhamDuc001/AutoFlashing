#!/bin/bash
SERIAL=${1}
adb -s $SERIAL shell cmd DiagAdb Configuration set display_config/display/touch_and_screen_configuration:11
sleep 5
adb -s $SERIAL shell cmd DiagAdb hardReset
sleep 75
adb -s $SERIAL shell wm size 2240x816  
sleep 5
adb -s $SERIAL reboot
sleep 35
adb -s $SERIAL shell setprop persist.log.tag VERBOSE
sleep 15
adb -s $SERIAL shell setprop persist.log.tag.jp.co.nissan.hmi.home.appmenu.utils.AppLauncherUtils S
sleep 15
adb -s $SERIAL shell setprop persist.log.tag.CarPackageManagerService S
sleep 15
adb -s $SERIAL shell cmd DiagAdb Configuration set hmi_config/comfort/aqs_clim:0
sleep 15
adb -s $SERIAL shell cmd DiagAdb Configuration set custom_assets_config_config/assets/custom_assets_config_4:'\"US\"'
sleep 15
adb -s $SERIAL reboot
sleep 35
for (( i = 0; i < 2; i++ )); do
  adb -s $SERIAL root
  sleep 15
  echo "qua cho root"
  adb -s $SERIAL shell setprop assetd.start routine_restart
  echo "qua cho routine"
  sleep 5
  adb -s $SERIAL reboot
  sleep 35
done