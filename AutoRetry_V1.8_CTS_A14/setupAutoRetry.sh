echo "lge@1234" | sudo -S apt-get install python3-tk
pip install watchdog
pip install pandas
pip install openpyxl
pip install pure-python-adb
pip install python-crontab
echo "lge@1234" | sudo -S cp canAT.rules /etc/udev/rules.d/
echo "lge@1234" | sudo -S chmod a+r /etc/udev/rules.d/
echo "lge@1234" | sudo -S service udev restart
