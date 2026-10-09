#!/bin/bash
SERIAL=${1}
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
  sleep 1
  adb -s $SERIAL reboot
  sleep 35
done
adb -s $SERIAL root
sleep 5
adb -s $SERIAL push test_keyboxes.xml /data/
sleep 5
adb -s $SERIAL push KmInstallKeybox /data/
sleep 5
adb -s $SERIAL shell chmod 655 /data/KmInstallKeybox
sleep 5
adb -s $SERIAL shell LD_LIBRARY_PATH=/vendor/lib64/hw:/vendor/lib64 /data/KmInstallKeybox /data/test_keyboxes.xml LGMC20180615115100069321 true
sleep 5
perl StoreKeybox.pl keybox.xml A-IVI2-200001 $SERIAL
sleep 5
adb -s $SERIAL root
sleep 15
echo "qua cho root"
adb -s $SERIAL shell setprop assetd.start routine_restart
echo "qua cho routine"
sleep 15
adb -s $SERIAL reboot
sleep 35
