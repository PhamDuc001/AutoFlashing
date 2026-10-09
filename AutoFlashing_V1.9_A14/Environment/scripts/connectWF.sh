#!/bin/bash
SERIAL=${1}
SSID=${2}
PWS=${3}
echo "[$SERIAL] Start connect wifi $SSID"
adb -s $SERIAL shell am start -n com.steinwurf.adbjoinwifi/.MainActivity -e ssid $SSID -e password_type WPA -e password $PWS

count2=0
until [[ $count2 -gt 10 ]]; do
	nam=$(adb -s $SERIAL shell ping -c1 www.google.com)
	if [[ -n "$nam" ]] ; then
		echo "[$SERIAL] Connected wifi $SSID"
		break;
	else
		adb -s $SERIAL shell am force-stop com.steinwurf.adbjoinwifi
		sleep 5
		adb -s $SERIAL shell am start -n com.steinwurf.adbjoinwifi/.MainActivity -e ssid $SSID -e password_type WPA -e password $PWS
		((count2++))
		echo "[$SERIAL] Try connect $SSID again: $count2"
	fi
	sleep 5
done
