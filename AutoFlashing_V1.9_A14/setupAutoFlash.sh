#!/bin/bash
python3 -m pip install --upgrade pip
sudo apt-get -y install python3-pandas
pip install pyarrow
echo "lge@1234" | sudo apt-get install aria2
echo "lge@1234" | sudo apt remove brltty
echo "lge@1234" | sudo -S cp 99-arduino.rules /etc/udev/rules.d/
echo "lge@1234" | sudo -S cp canAT.rules /etc/udev/rules.d/
echo "lge@1234" | sudo -S chmod a+r /etc/udev/rules.d/
echo "lge@1234" | sudo -S service udev restart
pip install pure-python-adb
pip install watchdog
pip install pyserial
pip install pexpect
echo "lge@1234" | sudo udevadm control --reload-rules && sudo udevadm trigger
