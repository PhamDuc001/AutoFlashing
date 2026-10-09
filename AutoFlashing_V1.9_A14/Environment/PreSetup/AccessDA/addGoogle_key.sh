#!/bin/bash
SERIAL=${1}
echo $SERIAL" Start reboot bootloader "
adb -s $SERIAL reboot bootloader
sleep 10
echo $SERIAL" Start flash devcfg_a ACCESSDA_reprovision_devcfg_auto.mbn"
fastboot -s $SERIAL flash devcfg_a ACCESSDA_reprovision_devcfg_auto.mbn
sleep 3
echo $SERIAL" reboot"
fastboot -s $SERIAL reboot
sleep 30
adb -s $SERIAL root
sleep 5
adb -s $SERIAL push test_keyboxes.xml /data/
sleep 1
adb -s $SERIAL push KmInstallKeybox /data/
sleep 1
adb -s $SERIAL shell chmod 655 /data/KmInstallKeybox
sleep 5
adb -s $SERIAL shell LD_LIBRARY_PATH=/vendor/lib64/hw:/vendor/lib64 /data/KmInstallKeybox /data/test_keyboxes.xml LGMC20180615115100069321 true
sleep 1
adb -s $SERIAL shell cmd DiagAdb Configuration set display_config/display/touch_and_screen_configuration:4
sleep 1
adb -s $SERIAL shell cmd DiagAdb setBootMode NORMAL
sleep 1
adb -s $SERIAL shell cmd DiagAdb hardReset
sleep 1
echo "DONE"
