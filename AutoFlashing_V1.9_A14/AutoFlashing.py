import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import tarfile
import logging
import threading
import time
import zipfile
from datetime import datetime

import pandas
import serial.tools.list_ports
from ppadb.client import Client
from serial import SerialException
from Object.devices import devices
from Object.FlashOJ import flashOJ

Micom_ver = None
Micom_expect = None
workSpace=None
filename = "AutoRetry_" + str(datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + ".log"
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#
# # create file handler
# fh = logging.FileHandler(filename)
# fh.setLevel(logging.DEBUG)
# fh.setFormatter(formatter)
# logger.addHandler(fh)
#
# # create console handler
# ch = logging.StreamHandler(sys.stdout)
# ch.setLevel(logging.INFO)
# ch.setFormatter(formatter)
# logger.addHandler(ch)
adb = Client(host="localhost", port=5037)
path_script = {}
path_script["pre_setup"] = None
path_script["update_micom"] = None
path_script["googleKey_AccessDA"] = None
path_script["Setup_AccessDA"] = None
path_script["Setup_NISSAN_DA"] = None
path_script["Setup_NISSAN_EU"] = None
path_script["googleKey_NISSAN_EU"] = None
path_script["googleKey_NISSAN_DA"] = None
path_script["custom_flash"] = None
path_script["gsi_image_file"] = None


def print_infomation(content):
    print(content)

def getMicomVerExpect(PathToFolderUserDebugBin):
    for filee in os.listdir(PathToFolderUserDebugBin):
        if filee.endswith(".txt") and os.path.isfile(os.path.join(PathToFolderUserDebugBin, filee)):
            temp = filee.split("_")[len(filee.split("_")) - 1]
            if temp.startswith("v"):
                temp = temp[1:len(temp) - 4]
                return temp

def copy_custom_flash_script(path):
    if os.path.exists(str(path_script["custom_flash"])):
        try:
            shutil.copy2(str(path_script["custom_flash"]), path)
        except Exception as e:
            print(e)


def run_script(path):
    print(color.BOLD + "Start run command: [{}]".format(path) + color.END)
    p1 = subprocess.Popen(path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # output, error = p1.communicate()
    for line in p1.stdout:
        print(line, end=' ')
    p1.wait()
    print(color.BOLD + "Complete command: [{}]".format(path) + color.END)


def check_adb_devices(serial):
    output = run_adb_command("adb devices")
    status = "FAIL"
    for line in output.splitlines():
        if str(line.split("\t")[0]).__contains__(serial):
            if line.endswith("device"):
                status = "PASS"
            elif line.endswith("recovery"):
                status = "RECOVERY"
            elif line.endswith("unauthorized"):
                status = "UNAUTHORIZED"
    return status


# def check_devices_state(serial):
#     try:
#         print("Get device_state")
#         output = run_adb_command("adb -s "+ serial +" get-state")
#     except Exception as e:
#         print("Try to get device_state")
#     return str(output)

def reload_adb_server():
    run_adb_command("adb kill-server")
    time.sleep(20)
    run_adb_command("adb devices")
    time.sleep(10)


def run_adb_command(command):
    print(color.BOLD + "Start run command: [{}]".format(command) + color.END)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    output, error = process.communicate()
    if not error is None:
        for line in error.decode("utf-8").split("\n"):
            print(line)
    if not output is None:
        for ot in output.decode("utf-8").split("\n"):
            print(ot)
    print(color.BOLD + "Complete run command: [{}]".format(command) + color.END)
    return output.decode("utf-8")

def ControlPCB(signal):
    try:
        ser = serial.Serial('/dev/arduino', 9600)
        num = bytes(str(signal), 'ascii')
        # print("Start enable USB DEBUG")
        ser.write(num)
        time.sleep(1)
        ser.close()
    except SerialException as e:
        print("Please plugin Virtual Keyboard")
        print(e)


def TurnOff_HU(device):
    print("Start Turn OFF HU serial: {}".format(device.serial))
    logger.info("Start Turn OFF HU serial: {}".format(device.serial))
    ControlPCB(device.rl_connect + "off")


def TurnOn_HU(device):
    print("Start Turn ON HU serial: {}".format(device.serial))
    logger.info("Start Turn ON HU serial: {}".format(device.serial))
    ControlPCB(device.rl_connect)


def KeyBoard_Enable_USB_Debug(device):
    print("Start Enable USBDebug for HU serial: {}".format(device.serial))
    logger.info("Start Enable USBDebug for HU serial: {}".format(device.serial))
    ControlPCB(device.kb_connect)


def KeyBoard_Allow_Privacy(device):
    print("Start Allow Privacy for HU serial: {}".format(device.serial))
    logger.info("Start Allow Privacy for HU serial: {}".format(device.serial))
    ControlPCB(device.kb_doubleClick)
def KeyBoard_Out_Recovery(device):
    print("Start Allow Privacy for HU serial: {}".format(device.serial))
    logger.info("Start Allow Privacy for HU serial: {}".format(device.serial))
    ControlPCB(device.kb_tribleClick)

def run_fastboot_command(command):
    print(color.BOLD + "Start run command: [{}]".format(command) + color.END)
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    output, error = process.communicate()
    if not error is None:
        for line in error.decode("utf-8").split("\n"):
            print(line)
    if not output is None:
        for ot in output.decode("utf-8").split("\n"):
            print(ot)
    print(color.BOLD + "Complete command: [{}]".format(command) + color.END)
    return output.decode("utf-8"), error.decode("utf-8")


def check_fastboot_device(seri):
    check = False
    output, error = run_fastboot_command("fastboot devices")
    for line in output.splitlines():
        if line.endswith("fastboot") or line.endswith("fastbootd"):
            if line.split()[0].__contains__(seri):
                check = True
                break
    return check


def fastboot_device(seri):
    output, error = run_fastboot_command("fastboot devices")
    devices = False
    for line in output.splitlines():
        if line.startswith(seri) and line.endswith("fastbootd"):
            devices = True
    return devices


def mtc_config_All_in_one(seri, typeProject, mtc_path, mtc_folder):
    print("Start MTC" + 'python3', mtc_folder + '/mtc_config.py', '-t', typeProject, '-p', mtc_path, '-s', seri)
    run_script(['cp','-r',path_script["mtc_python"], mtc_folder])
    change_curr_dir_work(mtc_folder)
    print(os.getcwd())
    try:
        run_script(['python3', mtc_folder + '/mtc_config.py', '-t', typeProject, '-p', mtc_path, '-s', seri])
    except Exception as e:
        print(e)


def addGooglekey(type, serial):
    print(color.BOLD + "====================[{}] Start add GoogleKey===========================".format(
        serial) + color.END)
    if str(type).__contains__("ACCESS_DA"):
        os.chdir(path_script["Setup_AccessDA"])
        run_script([path_script["googleKey_AccessDA"], serial])
    elif str(type).__contains__("NISSAN"):
        os.chdir(path_script["Setup_{}".format(type)])
        run_script([path_script["googleKey_{}".format(type)], serial])
    print(color.BOLD + "====================[{}] Finish add GoogleKey===========================".format(
        serial) + color.END)

def changeLanguage(type, serial):
    print(color.BOLD + "====================[{}] Start add ChangeLanguage===========================".format(
        serial) + color.END)
    os.chdir(path_script["Setup_{}".format(type)])
    run_script([path_script["changeLanguage_{}".format(type)], serial])
    print(color.BOLD + "====================[{}] Finish add ChangeLanguage===========================".format(
        serial) + color.END)

def run_command_SetupFolder(type, command):
    if type == "ACCESS_DA":
        os.chdir(path_script["Setup_AccessDA"])
        run_fastboot_command(command)
    elif type == "NISSAN_EU":
        os.chdir(path_script["Setup_NISSAN_EU"])
        run_fastboot_command(command)
    elif type == "NISSAN_DA":
        os.chdir(path_script["Setup_NISSAN_DA"])
        run_fastboot_command(command)
    else:
        os.chdir(type)
        run_fastboot_command(command)


def dump_logcat(connection):
    global Micom_ver
    while True:
        logger.info("Logcat listening.....")
        print("Logcat listening.....")
        data = connection.read(1024)
        if not data:
            break
        if str(data.decode('utf-8')).startswith("NADUBO"):
            Micom_ver = str(data.decode('utf-8')).split("_")[1]
            Micom_ver = Micom_ver.split(" ")[2]
            break
    connection.close()


def updateMicom(dev):
    for i in range(2):
        KeyBoard_Allow_Privacy(dev)
        time.sleep(5)
        KeyBoard_Allow_Privacy(dev)
        time.sleep(5)
        TurnOff_HU(dev)
        time.sleep(5)
        TurnOn_HU(dev)
        time.sleep(70)
    print(color.BOLD + "====================[{}] Start Update MICOM VER===========================".format(
        dev.serial) + color.END)
    global workspace
    os.chdir(workSpace + "/Environment/scripts")
    count = 10
    while count > 0:
        logger.info("UPDATE MICOM")
        run_adb_command("adb -s {} uninstall com.example.updatemicom".format(dev.serial))
        time.sleep(5)
        run_adb_command("adb -s {} uninstall com.example.updatemicom.test".format(dev.serial))
        time.sleep(5)
        run_adb_command("adb -s {} install -r -g -t updateMicom.apk".format(dev.serial))
        time.sleep(5)
        run_adb_command("adb -s {} install -r -g -t updateMicom-androidTest.apk".format(dev.serial))
        time.sleep(5)
        run_adb_command("adb -s {} shell input keyevent 4".format(dev.serial))
        run_adb_command("adb -s {} shell input keyevent 4".format(dev.serial))
        run_adb_command("adb -s {} shell input keyevent 4".format(dev.serial))
        run_adb_command("adb -s {} shell input keyevent 4".format(dev.serial))
        time.sleep(5)
        run_adb_command(
            "adb -s " + dev.serial + " shell am instrument -w -e class 'com.example.updatemicom.ExampleInstrumentedTest#updateMicom' com.example.updatemicom.test/androidx.test.runner.AndroidJUnitRunner")
        time.sleep(5)
        run_adb_command("adb -s {} shell cmd DiagAdb hardReset".format(dev.serial))
        wait_adbDevices_afterReboot(dev)
        time.sleep(60)
        KeyBoard_Allow_Privacy(dev)
        time.sleep(10)
        run_adb_command("adb -s {} logcat -c".format(dev.serial))
        line = run_adb_command(
            "adb -s {} shell am instrument -w -e class 'com.example.updatemicom.ExampleInstrumentedTest#getMicomVer' com.example.updatemicom.test/androidx.test.runner.AndroidJUnitRunner".format(
                dev.serial))
        global Micom_ver
        try:
            Micom_ver = str(line.split(":")[2])
        except Exception as e:
            print(e.__traceback__.tb_lineno)
            logger.error(e)
            logger.error(e.__traceback__.tb_lineno)
        try:
            if Micom_ver.__contains__(Micom_expect):
                logger.info("DONE update micom")
                print("DONE update micom: ", Micom_ver)
                break
            else:
                logger.info("Update micom version FAILED")
                logger.info("Try again")
                print("Update micom version FAILED")
                print("Try again")
        except Exception as e:
            print(e)
        count -= 1

    print(color.BOLD + "====================[{}] Finish Update MICOM VER===========================".format(
        dev.serial) + color.END)


def precondition(seri):
    global workspace
    os.chdir(workSpace + "/Environment/scripts")
    run_script([path_script["pre_setup"], seri, "GG", "11111112"])
def allowPrivacyAccess(seri):
    global workspace
    os.chdir(workSpace + "/Environment/scripts")
    precondition(seri)
    run_adb_command("adb -s {} install -r -g -t LGEDV_Change_Language.apk".format(seri))
    run_adb_command("adb -s {} install -r -g -t LGEDV_Change_Language-androidTest.apk".format(seri))
    time.sleep(5)
    run_adb_command(
        "adb -s {} shell am instrument -w -e class 'com.lgedv.changelanguage.ExampleInstrumentedTest#allowPrivacy' com.lgedv.changelanguage.test/androidx.test.runner.AndroidJUnitRunner".format(seri))
    time.sleep(100)
def auto_flash_userdebug(devi, list, workSpace,sw_path):
    print(color.BOLD + "====================[{}] Start Flashing UserDebug Binary===========================".format(
        devi.serial) + color.END)
    listdir = list
    change_curr_dir_work(listdir['userDebug_folder'])
    typeProject = None
    run_fastboot_command("adb -s {} reboot bootloader".format(devi.serial))
    wait_fastboot_devices(devi.serial)
    if str(listdir["model"]).__contains__("ACCESS_DA"):
        run_script(
            [listdir['userDebug_folder'] + "/flash_custom_nabo.sh", devi.serial, "fastboot_accessda_blank_flash.bat"])
        run_fastboot_command("fastboot -s {} reboot".format(devi.serial))
        wait_adbDevices_afterReboot(devi)
        time.sleep(20)
        change_curr_dir_work(listdir['mtc_config'])
        mtc_config_All_in_one(devi.serial, listdir["model"], listdir['mtc_config'] + "/push_vehicle_config.sh",
                              listdir['mtc_config'])
        wait_adbDevices_afterReboot(devi)
        time.sleep(20)
        KeyBoard_Allow_Privacy(devi)
        time.sleep(5)
        KeyBoard_Allow_Privacy(devi)
        time.sleep(5)
        addGooglekey(listdir["model"], devi.serial)
        wait_adbDevices_afterReboot(devi)
        time.sleep(10)
        updateMicom(devi)
    elif str(listdir["model"]).__contains__("NISSAN_EU"):
        run_script(
            [listdir['userDebug_folder'] + "/flash_custom_nabo.sh", devi.serial, "fastboot_n_fullnavi_blank_flash.bat"])
        run_fastboot_command("fastboot -s {} reboot".format(devi.serial))
        wait_adbDevices_afterReboot(devi)
        change_curr_dir_work(workSpace + "/Environment/scripts")
        time.sleep(5)
        addGooglekey(listdir["model"], devi.serial)
        wait_adbDevices_afterReboot(devi)
        time.sleep(10)
        mtc_config_All_in_one(devi.serial, listdir["model"], listdir["mtc_config"], sw_path)
        wait_adbDevices_afterReboot(devi)  
        changeLanguage(listdir["model"], devi.serial)      
        time.sleep(20)
        KeyBoard_Allow_Privacy(devi)
        time.sleep(5)
        KeyBoard_Allow_Privacy(devi)
        time.sleep(5)
        updateMicom(devi)
    elif str(listdir["model"]).__contains__("NISSAN_DA"):
        run_script(
            [listdir['userDebug_folder'] + "/flash_custom_nabo.sh", devi.serial, "fastboot_n_da2_r_blank_flash.bat"])
        run_fastboot_command("fastboot -s {} reboot".format(devi.serial))
        wait_adbDevices_afterReboot(devi)
        change_curr_dir_work(workSpace + "/Environment/scripts")
        time.sleep(5)
        mtc_config_All_in_one(devi.serial, listdir["model"], listdir["mtc_config"],sw_path)
        wait_adbDevices_afterReboot(devi)
        time.sleep(20)
        KeyBoard_Allow_Privacy(devi)
        time.sleep(5)
        KeyBoard_Allow_Privacy(devi)
        time.sleep(5)
        addGooglekey(listdir["model"], devi.serial)
        wait_adbDevices_afterReboot(devi)
        time.sleep(10)
        updateMicom(devi)
    print(color.BOLD + "====================[{}] Finish Flashing UserDebug Binary===========================".format(
        devi.serial) + color.END)


def enable_usb_debug(dev):
    count = 0
    while (not check_adb_devices(dev.serial).__eq__("PASS")) :
        wait_adbDevices_afterReboot(dev)
        time.sleep(30)
        KeyBoard_Allow_Privacy(dev)
        time.sleep(15)
        count_break = 1
        while (not check_adb_devices(dev.serial).__eq__("PASS")) and count_break < 10:
            print("Try to enable USB Debug {}".format(count_break))
            TurnOff_HU(dev)
            time.sleep(5)
            TurnOn_HU(dev)
            time.sleep(70)
            KeyBoard_Enable_USB_Debug(dev)
            time.sleep(10)
            count_break += 1
        if dev.typeOfDevices == "ACCESS_DA":
            allowPrivacyAccess(dev.serial)
        time.sleep(180)
        if count == 4:
            break
        TurnOff_HU(dev)
        time.sleep(5)
        TurnOn_HU(dev)
        time.sleep(70)
        if check_adb_devices(dev.serial).__eq__("UNAUTHORIZED"):
            count_break2 = 0
            while (not check_adb_devices(dev.serial).__eq__("PASS")) and count_break2 < 5:
                print("Try to enable USB Debug {}".format(count_break))
                TurnOff_HU(dev)
                time.sleep(5)
                TurnOn_HU(dev)
                time.sleep(30)
                KeyBoard_Enable_USB_Debug(dev)
                if dev.typeOfDevices == "ACCESS_DA":
                    allowPrivacyAccess(dev.serial)
                time.sleep(180)
                TurnOff_HU(dev)
                time.sleep(5)
                TurnOn_HU(dev)
                time.sleep(70)
                count_break2 += 1

            # run_adb_command("adb -s {} reboot bootloader".format(dev.serial))
            # wait_fastboot_devices(dev.serial)
            # run_fastboot_command("fastboot -s {} erase userdata".format(dev.serial))
            # run_fastboot_command("fastboot -s {} reboot".format(dev.serial))
            count += 1
        elif check_adb_devices(dev.serial).__eq__("PASS"):
            break


def auto_flash_user(dev, list, testItem):
    print(color.BOLD + "====================[{}] Start Flashing User Binary===========================".format(
        dev.serial) + color.END)
    listdir = list
    change_curr_dir_work(listdir['user_folder'])
    run_fastboot_command("adb -s {} reboot bootloader".format(dev.serial))
    wait_fastboot_devices(dev.serial)
    if str(listdir["model"]).__contains__("ACCESS_DA"):
        run_script([listdir['user_folder'] + "/flash_custom_nabo.sh", dev.serial, "fastboot_accessda_reflash.bat"])
        run_fastboot_command("fastboot -s {} flashing lock".format(dev.serial))
        # run_fastboot_command("fastboot reboot")
        enable_usb_debug(dev)
        precondition(dev.serial)
    elif str(listdir["model"]).__contains__("NISSAN_EU"):
        run_script([listdir['user_folder'] + "/flash_custom_nabo.sh", dev.serial, "fastboot_n_fullnavi_reflash.bat"])
        if testItem == "CTS" or testItem == "STS" or testItem == "ATS":
            run_fastboot_command(
                "fastboot -s " + dev.serial + " flash oem_a " + path_script[
                    "Setup_{}".format(listdir["model"])] + "oem_imag.bin")
            run_fastboot_command("fastboot -s {} flashing lock".format(dev.serial))
            wait_adbDevices_afterReboot(dev)
            time.sleep(20)
            enable_usb_debug(dev)
        else:
            output, error = run_fastboot_command("fastboot -s {} flashing unlock".format(dev.serial))
            if error.__contains__("already"):
                run_fastboot_command("fastboot -s {} reboot".format(dev.serial))
    elif str(listdir["model"]).__contains__("NISSAN_DA"):
        run_script([listdir['user_folder'] + "/flash_custom_nabo.sh", dev.serial, "fastboot_n_da2_reflash.bat"])
        if testItem == "CTS" or testItem == "STS" or testItem == "ATS":
            run_fastboot_command("fastboot -s " + dev.serial + " reboot")
            wait_adbDevices_afterReboot(dev)
            time.sleep(20)
            enable_usb_debug(dev)
            run_adb_command("adb -s {} reboot fastboot".format(dev.serial))
            run_command_SetupFolder(listdir["user_folder"], "fastboot -s {} flash boot_a boot.img".format(dev.serial))
            run_fastboot_command("fastboot -s {} reboot bootloader".format(dev.serial))
            time.sleep(10)
            run_fastboot_command("fastboot -s {} flashing lock".format(dev.serial))
            wait_adbDevices_afterReboot(dev)
            time.sleep(20)
            enable_usb_debug(dev)
        else:
            output, error = run_fastboot_command("fastboot -s {} flashing unlock".format(dev.serial))
            if error.__contains__("already"):
                run_fastboot_command("fastboot -s {} reboot".format(dev.serial))

    print(color.BOLD + "====================[{}] Finish Flashing User Binary===========================".format(
        dev.serial) + color.END)


def flash_CTS(devi, dict, workSpace, testItem,sw_path):
    auto_flash_userdebug(devi, dict, workSpace,sw_path)
    time.sleep(60)
    auto_flash_user(devi, dict, testItem)


def flash_ATS(devi, dict, workSpace, testItem,sw_path):
    auto_flash_userdebug(devi, dict, workSpace,sw_path)
    time.sleep(60)
    run_adb_command("adb -s {} shell cmd DiagAdb Configuration set hmi_config/comfort/hvactype:3".format(devi.serial))
    time.sleep(60)
    auto_flash_user(devi, dict, testItem)


def flash_VTS(devi, dict, workSpace, testItem,sw_path):
    auto_flash_userdebug(devi, dict, workSpace,sw_path)
    time.sleep(60)
    auto_flash_user(devi, dict, testItem)
    enable_usb_debug(devi)
    run_fastboot_command("adb -s {} reboot fastboot".format(devi.serial))
    wait_fastboot_devices(devi.serial)
    run_command_SetupFolder(dict["user_folder"], "fastboot -s {} flash boot_a boot-debug.img".format(devi.serial))
    time.sleep(5)
    run_fastboot_command("fastboot -s {} reboot".format(devi.serial))
    wait_adbDevices_afterReboot(devi)
    run_fastboot_command("adb -s {} reboot fastboot".format(devi.serial))
    wait_fastboot_devices(devi.serial)
    run_command_SetupFolder(dict["gsi_image_folder"], "fastboot -s {} erase system_a".format(devi.serial))
    time.sleep(5)
    run_command_SetupFolder(dict["gsi_image_folder"],
                            "fastboot -s {} flash -S 250M system_a system.img".format(devi.serial))
    time.sleep(5)
    run_command_SetupFolder("NISSAN_EU", "fastboot -s {} flash oem_a oem_imag.bin".format(devi.serial))
    time.sleep(5)
    run_fastboot_command("fastboot -s {} -w".format(devi.serial))
    time.sleep(5)
    run_fastboot_command("fastboot -s {} reboot".format(devi.serial))
    time.sleep(60)
    enable_usb_debug(devi)
    precondition(devi.serial)


def flash_GSI(devi, dict, workSpace, testItem,sw_path):
    auto_flash_userdebug(devi, dict, workSpace,sw_path)
    time.sleep(60)
    run_adb_command("adb -s {} root".format(devi.serial))
    time.sleep(2)
    run_adb_command("adb -s {} shell setprop assetd.start routine_restart".format(devi.serial))
    run_adb_command("adb -s {} reboot".format(devi.serial))
    wait_adbDevices_afterReboot(devi)
    auto_flash_user(devi, dict, testItem)
    enable_usb_debug(devi)
    run_fastboot_command("adb -s {} reboot fastboot".format(devi.serial))
    wait_fastboot_devices(devi.serial)
    print("user_folder: {}".format(dict["user_folder"]))
    run_command_SetupFolder(dict["user_folder"], "fastboot -s {} flash boot_a boot-debug.img".format(devi.serial))
    time.sleep(5)
    run_command_SetupFolder(dict["user_folder"], "fastboot -s {} flash boot_b boot-debug.img".format(devi.serial))
    time.sleep(5)
    run_fastboot_command("fastboot -s {} reboot".format(devi.serial))
    wait_adbDevices_afterReboot(devi)
    enable_usb_debug(devi)
    run_fastboot_command("adb -s {} reboot fastboot".format(devi.serial))
    wait_fastboot_devices(devi.serial)
    run_command_SetupFolder(dict["gsi_image_folder"], "fastboot -s {} erase system_a".format(devi.serial))
    time.sleep(5)
    run_command_SetupFolder(dict["gsi_image_folder"],
                            "fastboot -s {} flash -S 250M system_a system.img".format(devi.serial))
    time.sleep(5)
    run_command_SetupFolder("NISSAN_EU", "fastboot -s {} flash oem_a oem_imag.bin".format(devi.serial))
    time.sleep(5)
    run_fastboot_command("fastboot -s {} reboot".format(devi.serial))
    wait_adbDevices_afterReboot(devi)
    enable_usb_debug(devi)
    run_fastboot_command("adb -s {} reboot fastboot".format(devi.serial))
    run_command_SetupFolder(dict["user_folder"], "fastboot -s {} flash boot_a boot.img".format(devi.serial))
    time.sleep(5)
    run_command_SetupFolder(dict["user_folder"], "fastboot -s {} flash boot_b boot.img".format(devi.serial))
    time.sleep(5)
    run_fastboot_command("fastboot -s {} reboot".format(devi.serial))
    wait_adbDevices_afterReboot(devi)
    time.sleep(20)
    enable_usb_debug(devi)
    precondition(devi.serial)


def flash_STS(devi, dict, workSpace,sw_path):
    auto_flash_userdebug(devi, dict, workSpace,sw_path)
    run_fastboot_command("adb -s {} reboot bootloader".format(devi.serial))
    time.sleep(20)
    run_command_SetupFolder(dict["model"], "fastboot -s {} flash oem_a oem_imag.bin".format(devi.serial))
    time.sleep(30)
    run_fastboot_command("fastboot -s {} flashing lock".format(devi.serial))
    time.sleep(30)
    precondition(devi.serial)


def wait_adbDevices_afterReboot(devi):
    while check_adb_devices(devi.serial) != "PASS":
        if check_adb_devices(devi.serial) == "RECOVERY":
            KeyBoard_Out_Recovery(devi)
            print("Waiting for [{}] reboot".format(devi.serial))
            logger.info("Waiting for [{}] reboot".format(devi.serial))
        elif check_adb_devices(devi.serial) == "UNAUTHORIZED":
            # print("Start enable usb debug [{}]".format(serial))
            # logger.info("Start enable usb debug [{}]".format(serial))
            break
        time.sleep(10)


def wait_fastboot_devices(serial):
    start_time = time.time()
    counter = 0
    while not check_fastboot_device(serial):
        print("Waiting for {} into fastboot mode".format(serial))
        logger.info("Waiting for {} into fastboot mode".format(serial))
        time.sleep(5)


def agrument():
    parser = argparse.ArgumentParser(description='parse an XML file')
    parser.add_argument('-s', '--sw', help='Path to sw')
    parser.add_argument('-p', '--plan', help='Path to plan')
    args = parser.parse_args()
    wp = os.getcwd()
    return args.sw,args.plan,wp


def check_unlock_flashing(serial):
    if run_adb_command("adb -s {} shell getprop ro.boot.vbmeta.device_state".format(serial)) == "unlocked\n":
        return True
    else:
        return False


def grant_permission(path):
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            try:
                os.chmod(os.path.join(path, f), os.stat.S_IXUSR | os.stat.S_IXGRP | os.stat.S_IXOTH)
            except Exception as e:
                print(e)
                logger.error(e)


def no_unzip_sw_image(path, dict_sw):
    global Micom_expect
    # Get path to user and userDebug sw
    print("Delete old binary folder")
    for dir in os.listdir(path):
        if os.path.isdir(os.path.join(path, dir)):
            # shutil.rmtree(os.path.join(path, dir))
            # print("remove ", dir)
            time.sleep(2)
    for dir in os.listdir(path):
        if dir.__contains__("YAK"):
            dict_sw["model"] = "NISSAN"
        elif dir.__contains__("ANT"):
            dict_sw["model"] = "ACCESS"
        if str(dir).__contains__("userdebug") and os.path.isfile(os.path.join(path, dir)) and str(dir).__contains__(
                "tar.gz"):
            # userDebugTar = tarfile.open(os.path.join(path, dir))
            try:
                os.mkdir(str(path) + "/" + "userDebug_folder")
            except Exception as e:
                print(e)
                logger.error(e)
            dict_sw["userDebug_folder"] = str(path + "/" + "userDebug_folder")
            try:
                print("Extract UserDebug binary")
                #   userDebugTar.extractall(dict_sw["userDebug_folder"])
                print()
            except Exception as e:
                print(e)
                logger.error(e)
            # userDebugTar.close()
            for dir in os.listdir(dict_sw["userDebug_folder"]):
                if os.path.isdir(os.path.join(dict_sw["userDebug_folder"], dir)):
                    dict_sw["userDebug_folder"] = os.path.join(dict_sw["userDebug_folder"], dir)
                    Micom_expect = getMicomVerExpect(dict_sw["userDebug_folder"])
                    break
        elif not str(dir).__contains__("user") and os.path.isfile(os.path.join(path, dir)) and str(dir).__contains__(
                "tar.gz"):
            # mtc_config = tarfile.open(os.path.join(path, dir))
            try:
                os.mkdir(str(path) + "/" + "mtc_config")
            except Exception as e:
                print(e)
                logger.error(e)
            dict_sw["mtc_config"] = str(path + "/" + "mtc_config")
            try:
                print(color.BOLD + "Extract MTC config" + color.END)
                # mtc_config.extractall(dict_sw["mtc_config"])
            except Exception as e:
                print(e)
                logger.error(e)
            # mtc_config.close()
        elif not str(dir).__contains__("userdebug") and str(dir).__contains__("user") and os.path.isfile(
                os.path.join(path, dir)) and str(dir).__contains__("tar.gz"):
            # userTar = tarfile.open(os.path.join(path, dir))
            try:
                os.mkdir(str(path) + "/" + "user_folder")
            except Exception as e:
                print(e)
                logger.error(e)
            dict_sw["user_folder"] = str(path + "/" + "user_folder")
            try:
                print("Extract User binary")
                # userTar.extractall(dict_sw["user_folder"])
            except Exception as e:
                print(e)
                logger.error(e)
            # userTar.close()
            for dir in os.listdir(dict_sw["user_folder"]):
                if os.path.isdir(os.path.join(dict_sw["user_folder"], dir)):
                    dict_sw["user_folder"] = os.path.join(dict_sw["user_folder"], dir)
                    break
        elif os.path.isfile(os.path.join(path, dir)) and str(dir).__contains__(".bat"):
            try:
                dict_sw["mtc_config"] = os.path.join(path, dir)
            except Exception as e:
                print(e)
                logger.error(e)
            try:
                dict_sw["sw"] = path
            except Exception as e:
                print(e)
                logger.error(e)
    if str(dict_sw["model"]).__eq__("ACCESS"):
        try:
            mtc_bash = open(dict_sw["mtc_config"] + "/push_vehicle_config.sh", "r")
            content = mtc_bash.readlines()
            mtc_bash.close()
        except Exception as e:
            print(e.__traceback__.tb_lineno)
        adding_arg = "IVI_ADB_SERIAL=${1}\n"
        content.insert(1, adding_arg)
        mtc_bash = open(dict_sw["mtc_config"] + "/push_vehicle_config.sh", "w")
        content = "".join(content)
        mtc_bash.write(content)
        mtc_bash.close()
    copy_custom_flash_script(dict_sw["userDebug_folder"])
    copy_custom_flash_script(dict_sw['user_folder'])


def unzip_sw_image(path, dict_sw, type):
    global Micom_expect
    dict_sw["model"] = type
    # Get path to user and userDebug sw
    print("Delete old binary folder")
    for dir in os.listdir(path):
        if os.path.isdir(os.path.join(path, dir)):
            shutil.rmtree(os.path.join(path, dir))
            print("remove ", dir)
            time.sleep(20)
    for dir in os.listdir(path):
        if str(dict_sw["model"]).__contains__("NISSAN") and path_script["gsi_image_file"] is not None:
            try:
                os.mkdir(str(path) + "/" + "gsi_image_folder")
            except Exception as e:
                print(e)
                logger.error(e)
            dict_sw["gsi_image_folder"] = str(path + "/" + "gsi_image_folder")
            try:
                with zipfile.ZipFile(path_script["gsi_image_file"], 'r') as gsi_file:
                    gsi_file.extractall(dict_sw["gsi_image_folder"])
            except Exception as e:
                print(e)
        if str(dir).__contains__("userdebug") and os.path.isfile(os.path.join(path, dir)) and str(dir).__contains__(
                "tar.gz"):
            userDebugTar = tarfile.open(os.path.join(path, dir))
            try:
                os.mkdir(str(path) + "/" + "userDebug_folder")
            except Exception as e:
                print(e)
                logger.error(e)
            dict_sw["userDebug_folder"] = str(path + "/" + "userDebug_folder")
            try:
                print("Extract UserDebug binary")
                userDebugTar.extractall(dict_sw["userDebug_folder"])
                print()
            except Exception as e:
                print(e)
                logger.error(e)
            userDebugTar.close()
            for dir in os.listdir(dict_sw["userDebug_folder"]):
                if os.path.isdir(os.path.join(dict_sw["userDebug_folder"], dir)):
                    dict_sw["userDebug_folder"] = os.path.join(dict_sw["userDebug_folder"], dir)
                    Micom_expect = getMicomVerExpect(dict_sw["userDebug_folder"])
                    break
        elif not str(dir).__contains__("user") and os.path.isfile(os.path.join(path, dir)) and str(dir).__contains__(
                "tar.gz") and (str(dir).__contains__(
            "vehicle") or str(dir).__contains__(
            "mtc")):
            mtc_config = tarfile.open(os.path.join(path, dir))
            try:
                os.mkdir(str(path) + "/" + "mtc_config")
            except Exception as e:
                print(e)
                logger.error(e)
            dict_sw["mtc_config"] = str(path + "/" + "mtc_config")
            try:
                print(color.BOLD + "Extract MTC config" + color.END)
                mtc_config.extractall(dict_sw["mtc_config"])
            except Exception as e:
                print(e)
                logger.error(e)
            mtc_config.close()
        elif not str(dir).__contains__("userdebug") and str(dir).__contains__("user") and os.path.isfile(
                os.path.join(path, dir)) and str(dir).__contains__("tar.gz"):
            userTar = tarfile.open(os.path.join(path, dir))
            try:
                os.mkdir(str(path) + "/" + "user_folder")
            except Exception as e:
                print(e)
                logger.error(e)
            dict_sw["user_folder"] = str(path + "/" + "user_folder")
            try:
                print("Extract User binary")
                userTar.extractall(dict_sw["user_folder"])
            except Exception as e:
                print(e)
                logger.error(e)
            userTar.close()
            for dir in os.listdir(dict_sw["user_folder"]):
                if os.path.isdir(os.path.join(dict_sw["user_folder"], dir)):
                    dict_sw["user_folder"] = os.path.join(dict_sw["user_folder"], dir)
                    break
        elif os.path.isfile(os.path.join(path, dir)) and str(dir).__contains__(".bat"):
            try:
                dict_sw["mtc_config"] = os.path.join(path, dir)
            except Exception as e:
                print(e)
                logger.error(e)
            try:
                dict_sw["sw"] = path
            except Exception as e:
                print(e)
                logger.error(e)
    if str(dict_sw["model"]).__contains__("ACCESS_DA"):
        try:
            mtc_bash = open(dict_sw["mtc_config"] + "/push_vehicle_config.sh", "r")
            content = mtc_bash.readlines()
            mtc_bash.close()
        except Exception as e:
            print(e.__traceback__.tb_lineno)
        adding_arg = "IVI_ADB_SERIAL=${1}\n"
        content.insert(1, adding_arg)
        mtc_bash = open(dict_sw["mtc_config"] + "/push_vehicle_config.sh", "w")
        content = "".join(content)
        mtc_bash.write(content)
        mtc_bash.close()
    copy_custom_flash_script(dict_sw["userDebug_folder"])
    copy_custom_flash_script(dict_sw['user_folder'])


def change_Oem_Image(pathUser, pathUserDebug, type):
    if str(type).__contains__("ACCESS_DA"):
        for file in os.listdir(pathUserDebug):
            if os.path.isfile(os.path.join(pathUserDebug, file)) and str(file).__eq__("oem.img"):
                try:
                    shutil.copy2(os.path.join(pathUserDebug, file), pathUser)
                except Exception as e:
                    print(e)
                    logger.error(e)
        for file in os.listdir(pathUser):
            if os.path.isfile(os.path.join(pathUser, file)) and str(file).__eq__("abl.elf"):
                try:
                    print("Remove abl.elf in user Folder")
                    os.remove(os.path.join(pathUser, file))
                except Exception as e:
                    print(e)
                    logger.error(e)
        for file in os.listdir(pathUser):
            if os.path.isfile(os.path.join(pathUser, file)) and str(file).__eq__("abl-debug.elf"):
                name = str(os.path.join(pathUser, file))
                try:
                    newName = name[:len(name) - 13] + "abl.elf"
                    run_script(["mv", name, newName])
                    print("Success change abl-debug.elf to abl.elf")
                    # os.rename(name, name[:len(name) - 13] + "abl.elf")
                except Exception as e:
                    print(e)
                    logger.error(e)
    elif str(type).__contains__("NISSAN_EU"):
        for file in os.listdir(pathUserDebug):
            if os.path.isfile(os.path.join(pathUserDebug, file)) and str(file).__eq__("oem.img"):
                try:
                    shutil.copy2(os.path.join(pathUserDebug, file), pathUser)
                except Exception as e:
                    print(e)
                    logger.error(e)
            if os.path.isfile(os.path.join(pathUserDebug, file)) and str(file).__eq__("userdata.img"):
                try:
                    os.remove(os.path.join(pathUserDebug, file))
                except Exception as e:
                    print(e)
                    logger.error(e)
        for file in os.listdir(pathUser):
            if os.path.isfile(os.path.join(pathUser, file)) and str(file).__eq__("abl.elf"):
                try:
                    print("Remove abl.elf in user Folder")
                    os.remove(os.path.join(pathUser, file))
                except Exception as e:
                    print(e)
                    logger.error(e)
        for file in os.listdir(pathUser):
            if os.path.isfile(os.path.join(pathUser, file)) and str(file).__eq__("abl-debug.elf"):
                name = str(os.path.join(pathUser, file))
                try:
                    newName = name[:len(name) - 13] + "abl.elf"
                    run_script(["mv", name, newName])
                    print("Success change abl-debug.elf to abl.elf")
                    # os.rename(name, name[:len(name) - 13] + "abl.elf")
                except Exception as e:
                    print(e)
                    logger.error(e)
            elif os.path.isfile(os.path.join(pathUser, file)) and str(file).__eq__("userdata_assets.img"):
                try:
                    shutil.copy2(os.path.join(pathUser, file), pathUserDebug + "/userdata.img")
                    print(
                        f"File copied and renamed successfully: {os.path.join(pathUser, file)} -> {pathUserDebug}/userdata.img")
                except Exception as e:
                    print(e)
                    logger.error(e)

    elif str(type).__eq__("NISSAN_DA"):
        for file in  os.listdir(pathUserDebug):
            if os.path.isfile(os.path.join(pathUserDebug, file)) and str(file).__eq__("oem.img"):
                try:
                    shutil.copy2(os.path.join(pathUserDebug, file), pathUser)
                except Exception as e:
                    print(e)
                    logger.error(e)
            if os.path.isfile(os.path.join(pathUserDebug, file)) and str(file).__eq__("userdata.img"):
                try:
                    os.remove(os.path.join(pathUserDebug, file))
                except Exception as e:
                    print(e)
                    logger.error(e)
        for file in os.listdir(pathUser):
            if os.path.isfile(os.path.join(pathUser, file)) and str(file).__eq__("abl.elf"):
                try:
                    print("Remove abl.elf in user Folder")
                    os.remove(os.path.join(pathUser, file))
                except Exception as e:
                    print(e)
                    logger.error(e)
        for file in os.listdir(pathUser):
            if os.path.isfile(os.path.join(pathUser, file)) and str(file).__eq__("abl-debug.elf"):
                name = str(os.path.join(pathUser, file))
                try:
                    newName=name[:len(name) - 13] + "abl.elf"
                    run_script(["mv",name,newName])
                    print("Success change abl-debug.elf to abl.elf")
                    #os.rename(name, name[:len(name) - 13] + "abl.elf")
                except Exception as e:
                    print(e)
                    logger.error(e)
            elif os.path.isfile(os.path.join(pathUser, file)) and str(file).__eq__("userdata_assets.img"):
                try:
                    shutil.copy2(os.path.join(pathUser, file), pathUserDebug + "/userdata.img")
                    print(
                        f"File copied and renamed successfully: {os.path.join(pathUser, file)} -> {pathUserDebug}/userdata.img")
                except Exception as e:
                    print(e)
                    logger.error(e)



def change_curr_dir_work(path):
    try:
        os.chdir(path)
        print("Change current workplace to {}".format(path))
        logger.info("Change current workplace to {}".format(path))
    except Exception as e:
        logger.error(e)


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
def makeFolderTest(path_to_sw_original,flash_oj,name_phase):
    try:
        os.mkdir(path_to_sw_original+"/{}".format(name_phase))
    except Exception as e:
        print(e)
        logger.error(e)
    newSW_folder = path_to_sw_original+"/{}".format(name_phase)
    for dir in os.listdir(path_to_sw_original):
        if os.path.isfile(os.path.join(path_to_sw_original,dir)):
            try:
                shutil.copy2(os.path.join(path_to_sw_original,dir),newSW_folder)
            except Exception as e:
                print(e)
                logger.error(e)
    try:
        shutil.copy2(flash_oj.mtc_ver,newSW_folder)
    except Exception as e:
        print(e)
        logger.error(e)
    return newSW_folder
def analysis_plan(filename,path_to_orignal_sw):
    if filename:
        try:
            filename = r"{}".format(filename)
            df = pandas.read_excel(filename, sheet_name="Sheet1", header=0,
                                   converters={'Project': str, 'Testsuite': str, 'Serial': str,'MTC_VERSION':str, 'DPI': str,
                                               'GSI': str})
            hashPlan = {}
            f = open('Environment/scripts/tool_define_struct.json')
            data = json.load(f)
            for index, row in df.iterrows():
                temp_flashOJ= flashOJ(row[0],row[1],row[2],row[3])
                temp_flashOJ.mtc_ver = "/home/lge/Environment/MTC/" + temp_flashOJ.project + "/" + row[3]
                if temp_flashOJ.project == "ACCESS_DA":
                    temp_flashOJ.dpi=row[4]
                    hashName = temp_flashOJ.project + "_" + temp_flashOJ.testSuite+"_"+temp_flashOJ.dpi
                else:
                    if row.iloc[5] != row.iloc[5]:
                        temp_flashOJ.gsi_ver=None
                    else:
                        temp_flashOJ.gsi_ver=row.iloc[5]
                    hashName = temp_flashOJ.project+"_"+temp_flashOJ.testSuite
                if hashPlan.__contains__(hashName):
                    hashPlan[hashName].add_devices(temp_flashOJ.serial_list)
                elif not hashPlan.__contains__(hashName):
                    toolPATH = makeFolderTest(path_to_orignal_sw, temp_flashOJ,hashName)
                    temp_flashOJ.sw_path=toolPATH
                    hashPlan.__setitem__(hashName,temp_flashOJ)
            return hashPlan

        except ValueError:
            logger.error("Plan File could not be opened")
            print("Plan File could not be opened")
        except FileNotFoundError:
            logger.error("Plan Excel File Not Found")
            print("Plan Excel File Not Found")
def main_thread(flash_oj):
    dict = {}
    path_to_sw=flash_oj.sw_path
    type_task=flash_oj.project
    testItem=flash_oj.testSuite
    dpi=flash_oj.dpi
    global workSpace
    gsiImageVersion=flash_oj.gsi_ver
    listt = []
    for i in str(flash_oj.serial_list).split("-"):
        tempD = devices()
        tempD.serial = str(i.split("_")[0])
        tempD.kb_connect = str(i.split("_")[1])
        tempD.rl_connect = str(i.split("_")[2])
        tempD.typeOfDevices=flash_oj.project
        tempD.setup()
        listt.append(tempD)
    listDevicesFlash = listt
    if workSpace.__eq__("None") or workSpace is None:
        workSpace = "/home/lge"
    path_script["pre_setup"] = str(workSpace) + "/Environment/scripts/Precondition.sh"
    path_script["update_micom"] = str(workSpace) + "/Environment/scripts/updateMicom.sh"
    path_script["googleKey_AccessDA"] = str(workSpace) + "/Environment/PreSetup/AccessDA/addGoogle_key.sh"
    path_script["Setup_AccessDA"] = str(workSpace) + "/Environment/PreSetup/AccessDA/"
    path_script["Setup_NISSAN_EU"] = str(workSpace) + "/Environment/PreSetup/NissanEU/"
    path_script["Setup_NISSAN_DA"] = str(workSpace) + "/Environment/PreSetup/NissanDA/"
    path_script["googleKey_NISSAN_EU"] = str(workSpace) + "/Environment/PreSetup/NissanEU/addGoogle_key_Nissan.sh"
    path_script["changeLanguage_NISSAN_EU"] = str(workSpace) + "/Environment/PreSetup/NissanEU/changeLanguage_Nissan.sh"
    path_script["googleKey_NISSAN_DA"] = str(workSpace) + "/Environment/PreSetup/NissanDA/addGoogle_key_Nissan.sh"
    path_script["custom_flash"] = str(workSpace) + "/Environment/scripts/flash_custom_nabo.sh"
    path_script["mtc_python"] = str(workSpace) + "/Environment/scripts/mtc_config.py"
    if gsiImageVersion is not None:
        path_script["gsi_image_file"] = "/home/lge/Environment/GSI_IMAGE/gsi_car_arm64-img-{}.zip".format(
            gsiImageVersion)
    if str(dpi) == "160":
        type_task = "ACCESS_DA_160"
    elif str(dpi) == "180":
        type_task = "ACCESS_DA_180"
    unzip_sw_image(path_to_sw, dict, type_task)
    # no_unzip_sw_image(path_to_sw, dict)
    time.sleep(1)
    change_Oem_Image(dict['user_folder'], dict['userDebug_folder'], type_task)
    time.sleep(1)
    if str(testItem) == "CTS":
        id_list = []
        for devi in listDevicesFlash:
            devi.setup()
            id = threading.Thread(target=flash_CTS, args=(devi, dict, workSpace, testItem, path_to_sw,))
            id_list.append(id)
            id.start()
            time.sleep(20)
        for temp_id in id_list:
            try:
                temp_id.join()
            except Exception as e:
                print(e)
    elif str(testItem) == "ATS":
        id_list = []
        for devi in listDevicesFlash:
            devi.setup()
            id = threading.Thread(target=flash_ATS, args=(devi, dict, workSpace, testItem, path_to_sw,))
            id_list.append(id)
            id.start()
            time.sleep(20)
        for temp_id in id_list:
            temp_id.join()
    elif str(testItem) == "STS":
        id_list = []
        for devi in listDevicesFlash:
            devi.setup()
            id = threading.Thread(target=flash_STS, args=(devi, dict, workSpace, path_to_sw,))
            id_list.append(id)
            id.start()
            time.sleep(20)
        for temp_id in id_list:
            temp_id.join()
    elif str(testItem) == "VTS":
        id_list = []
        for devi in listDevicesFlash:
            devi.setup()
            id = threading.Thread(target=flash_VTS, args=(devi, dict, workSpace, testItem, path_to_sw,))
            id_list.append(id)
            id.start()
            time.sleep(20)
        for temp_id in id_list:
            temp_id.join()
    elif str(testItem) == "GSI":
        id_list = []
        for devi in listDevicesFlash:
            devi.setup()
            id = threading.Thread(target=flash_GSI, args=(devi, dict, workSpace, testItem, path_to_sw,))
            id_list.append(id)
            id.start()
            time.sleep(20)
        for temp_id in id_list:
            temp_id.join()
    elif str(testItem) == "ONLY_USERDEBUG":
        id_list = []
        for devi in listDevicesFlash:
            devi.setup()
            id = threading.Thread(target=auto_flash_userdebug, args=(devi, dict, workSpace, path_to_sw,))
            id_list.append(id)
            id.start()
            time.sleep(20)
        for temp_id in id_list:
            temp_id.join()
    elif str(testItem) == "ONLY_USER":
        id_list = []
        for devi in listDevicesFlash:
            devi.setup()
            id = threading.Thread(target=auto_flash_user, args=(devi, dict, testItem, path_to_sw,))
            id_list.append(id)
            id.start()
            time.sleep(20)
        for temp_id in id_list:
            temp_id.join()
    elif str(testItem) == "ONLY_MTC":
        id_list = []
        for devi in listDevicesFlash:
            devi.setup()
            id = threading.Thread(target=mtc_config_All_in_one,
                                  args=(devi.serial, dict["model"], dict["mtc_config"], path_to_sw,))
            id_list.append(id)
            id.start()
            time.sleep(20)
        for temp_id in id_list:
            temp_id.join()
    print("FINISH FLASHING")
    print("""
        ███████╗██╗███╗   ██╗██╗███████╗██╗  ██╗
        ██╔════╝██║████╗  ██║██║██╔════╝██║  ██║
        █████╗  ██║██╔██╗ ██║██║███████╗███████║
        ██╔══╝  ██║██║╚██╗██║██║╚════██║██╔══██║
        ██║     ██║██║ ╚████║██║███████║██║  ██║
        ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝╚══════╝╚═╝  ╚═╝

        """)

if __name__ == '__main__':
    path_to_sw,path_plan,workSpace=agrument()
    list_of_plan = analysis_plan(path_plan, path_to_sw)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=6)
    for tempRound in list_of_plan:
        temp = list_of_plan.get(tempRound)
        #main_thread(temp)
        pool.submit(main_thread, (temp))
