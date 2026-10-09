#!/bin/bash
SERIAL=${1}
adb -s $SERIAL root
sleep 2
adb -s $SERIAL push test_keyboxes.xml /data/
sleep 2
adb -s $SERIAL push KmInstallKeybox /data/
sleep 2
adb -s $SERIAL shell chmod 655 /data/KmInstallKeybox
sleep 2
adb -s $SERIAL shell LD_LIBRARY_PATH=/vendor/lib64/hw:/vendor/lib64 /data/KmInstallKeybox /data/test_keyboxes.xml LGMC20180615115100069321 true
sleep 2
perl StoreKeybox.pl keybox.xml A-IVI2-200001 $SERIAL
sleep 2
adb -s $SERIAL shell cmd DiagAdb Configuration set display_config/display/touch_and_screen_configuration:11
sleep 10
adb -s $SERIAL shell wm size 1920x720
sleep 10
adb -s $SERIAL shell cmd DiagAdb hardReset
sleep 20
