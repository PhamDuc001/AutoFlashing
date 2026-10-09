#!/bin/bash
SERIAL=${1}

adb -s $SERIAL root
sleep 5
adb -s $SERIAL shell "setprop vendor.serialno $SERIAL"
sleep 5
adb -s $SERIAL push test_keyboxes.xml /data/
sleep 5
adb -s $SERIAL shell "KmInstallKeybox /data/test_keyboxes.xml LGMC20180615115100069321 true"
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
adb -s $SERIAL wait-for-device
