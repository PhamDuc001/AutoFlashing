#!/bin/bash
SERIAL=${1}
SSID=${2}
PWS=${3}
workSpace=$PWD
echo $workSpace
adb -s $SERIAL install -r -g -t $PWD"/"wifi.apk
adb -s $SERIAL install -r -g -t $PWD"/"LGEDV_Change_Language-androidTest.apk
adb -s $SERIAL install -r -g -t $PWD"/"LGEDV_Change_Language.apk
#adb install -r -g -t $PWD"/"checkCanat-androidTest.apk
#adb install -r -g -t $PWD"/"checkCanat.apk
count2=0
until [[ $count2 -gt 10 ]]; do
	nam=$(adb -s $SERIAL shell ping -c1 www.google.com)
	if [[ -n "$nam" ]] ; then
		echo "[$SERIAL]Wifi Connected"
		break;
	else
		adb -s $SERIAL shell am force-stop com.steinwurf.adbjoinwifi
		sleep 5
		adb -s $SERIAL shell am start -n com.steinwurf.adbjoinwifi/.MainActivity -e ssid $SSID -e password_type WPA -e password $PWS
		((count2++))
		echo "[$SERIAL]Try connect WIFI again: $count2"
	fi
	sleep 5
done
adb -s $SERIAL shell input keyevent 4 #BACK
adb -s $SERIAL shell input keyevent 4 #BACK
adb -s $SERIAL shell input keyevent 3 #HOME
echo "[$SERIAL] Start setting non Lockscreen"
check_lockscreen=$(adb -s $SERIAL shell settings get secure lock_screen_lock_none)
if [[ $check_lockscreen == "true" ]];then
	echo "[$SERIAL] Already non Lockscreen"
else
	for (( i = 0; i < 3; i++ )); do
		echo "[$SERIAL] Setting non lockscreen "$i
		adb -s $SERIAL shell settings put secure lock_screen_lock_none true #LOCKSCREN
		lockscreen=$(adb -s $SERIAL shell settings get secure lock_screen_lock_none)
		if [[ $lockscreen == "true" ]] ; then	
			echo "[$SERIAL] Setting non Lockscreen Done"
			break;
		fi
	done
fi
echo "[$SERIAL] Start setting enable Stayawake"
check_stayawake=$(adb -s $SERIAL shell settings get global stay_on_while_pulgged_in)
if [[ $check_stayawake == "7" ]];then
	echo "[$SERIAL] Already enable StayAwake"
else
	for (( i = 0; i < 3; i++ )); do
		echo "[$SERIAL] Setting enable Stayawake "$i
		adb -s $SERIAL shell settings put global stay_on_while_pulgged_in 7 #STAY_AWAKE
		stayawake=$(adb -s $SERIAL shell settings get global stay_on_while_pulgged_in)
		if [[ $stayawake == "7" ]] ; then	
			echo "[$SERIAL] Setting enable StayAwake Done"
			break;
		fi
	done
fi
echo "[$SERIAL] Start setting timedate format"
check_timedate=$(adb -s $SERIAL shell settings get system time_12_24)
if [[ $check_timedate == "12" ]];then
	echo "[$SERIAL] Already setting timedate format 12"
else
	for (( i = 0; i < 3; i++ )); do
		echo "[$SERIAL] Setting timedate format 12 "$i
		adb -s $SERIAL shell settings put system time_12_24 12 #time_date format
		timedate=$(adb -s $SERIAL shell settings get system time_12_24)
		if [[ $timedate == "12" ]] ; then	
			echo "[$SERIAL] Setting timedate format 12 Done"
			break;
		fi
	done
fi
check_language=$(adb -s $SERIAL shell getprop persist.sys.locale)
if [[ $check_language == "en-US" ]];then
	echo "[$SERIAL] Already in English US"
else
	for (( i = 0; i < 3; i++ )); do
		echo "[$SERIAL] Change Language to English US "$i
		adb -s $SERIAL shell am instrument -w -e class 'com.lgedv.changelanguage.ExampleInstrumentedTest#changetoEN' com.lgedv.changelanguage.test/androidx.test.runner.AndroidJUnitRunner
		language=$(adb -s $SERIAL shell getprop persist.sys.locale)
		if [[ $language == "en-US" ]] ; then
			echo "[$SERIAL] Change Language to English US Done"
			break;
		fi
	done
fi
echo "[$SERIAL] Uninstall change language"
adb -s $SERIAL uninstall com.lgedv.changelanguage
adb -s $SERIAL uninstall com.lgedv.changelanguage.test


