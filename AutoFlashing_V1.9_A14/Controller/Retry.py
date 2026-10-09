import argparse
import logging

from ppadb.client import Client
import xml.etree.ElementTree as ET
import subprocess
from Object.devices import devices

def agruments():
    parser = argparse.ArgumentParser(description='parse an XML file')
    parser.add_argument('-p', '--test_result', help='Path to XML file')
    parser.add_argument('-t', '--runType', type=str, help='Number of retry')
    parser.add_argument('-r', '--ssRetry', type=int, help='Number of retry')
    parser.add_argument('-ip', '--serverIP', help="IP's windows PC")
    parser.add_argument('-m', '--module', help="Module name")
    parser.add_argument('-s', '--session', help="Session name")
    parser.add_argument('-can', '--CanDevices', help="Session name")
    parser.add_argument('-list', '--DevicesList', help="Session name")
    args = parser.parse_args()
    return int(args.ssRetry), args.runType, args.module, args.test_result, args.serverIP, args.session,args.CanDevices,args.DevicesList

def getDeviceInfo(tooltype):
    adb = Client(host="localhost", port=5037)
    list = []
    for dev in adb.devices():
        tempD = devices()
        tempD.fingerprint = dev.shell("getprop ro.system.build.fingerprint")
        strT = dev.shell("getprop ro.boot.vbmeta.device_state")
        rootStatus = dev.shell("getprop ro.debuggable")
        tempD.serial = dev.serial
        if tooltype.__contains__("sts") and str(tempD.fingerprint).__contains__("userdebug") and str(strT).__contains__(
                "locked"):
            tempD.typeOfDevices = "STS"
            list.append(tempD)
        elif tooltype.__contains__("cts") and not str(tempD.fingerprint).__contains__("userdebug") and not str(
                tempD.fingerprint).__contains__("gsi") and str(strT).__contains__("locked"):
            tempD.typeOfDevices = "CTS"
            list.append(tempD)
        elif tooltype.__contains__("cts-on-gsi") and str(tempD.fingerprint).__contains__("gsi") and str(
                rootStatus).__contains__("0") and str(strT).__contains__("unlocked"):
            tempD.typeOfDevices = "GSI"
            list.append(tempD)
        elif tooltype.__contains__("vts") and str(tempD.fingerprint).__contains__("gsi") and str(
                rootStatus).__contains__("1") and str(strT).__contains__("unlocked"):
            tempD.typeOfDevices = "VTS"
            list.append(tempD)
    return list


def MakeSerialStr(listDevices):
    temp = "--shard-count "+str(len(listDevices))
    for ser in listDevices:
        temp += (" -s " + str(ser))
    return temp


def sendCommand(listSerial, typeOfRun, timeRetry, sessionName):
    if typeOfRun == "MULTIPLE":
        print("[NaBo] Run Retry Mode MULTIPLE")
        logging.info("[NaBo] Run Retry Mode MULTIPLE")
        if timeRetry < 2:
            tmux_send = subprocess.Popen(['tmux', 'send-keys', '-t', sessionName,
                                          'run retry --retry ' + str(
                                              timeRetry) + ' --retry-type FAILED ' + str(listSerial),
                                          'Enter'])
            tmux_send.wait()
            print("[NaBo] Send retry command success ^^")
            logging.info("[NaBo] Send retry command success ^^")
            print('run retry --retry ' + str(timeRetry) + ' --retry-type FAILED ' + str(listSerial))
            logging.info('run retry --retry ' + str(timeRetry) + ' --retry-type FAILED ' + str(listSerial))
        elif timeRetry == 2:
            tmux_send = subprocess.Popen(
                ['tmux', 'send-keys', '-t', sessionName,
                 'run retry --retry ' + str(timeRetry) + ' --retry-type NOT_EXECUTED ' + str(listSerial),
                 'Enter'])
            tmux_send.wait()
            print("[NaBo] Send retry command success ^^")
            logging.info("[NaBo] Send retry command success ^^")
            print('run retry --retry ' + str(timeRetry) + ' --retry-type NOT_EXECUTED ' + str(listSerial))
            logging.info('run retry --retry ' + str(timeRetry) + ' --retry-type NOT_EXECUTED ' + str(listSerial))
        else:
            tmux_send = subprocess.Popen(
                ['tmux', 'send-keys', '-t', sessionName,
                 ' run retry --retry ' + str(timeRetry) + ' --retry-type FAILED ' + str(listSerial),
                 'Enter'])
            tmux_send.wait()
            print("[NaBo] Send retry command success ^^")
            logging.info("[NaBo] Send retry command success ^^")
            print('run retry --retry ' + str(timeRetry) + ' --retry-type FAILED ' + str(listSerial))
            logging.info('run retry --retry ' + str(timeRetry) + ' --retry-type FAILED ' + str(listSerial))
    else:
        print("[NaBo] Run Retry Mode SINGLE")
        logging.info("[NaBo] Run Retry Mode SINGLE")
        tmux_send = subprocess.Popen(
            ['tmux', 'send-keys', '-t', sessionName,
             ' run retry --retry ' + str(timeRetry) + ' --retry-type FAILED ' + str(listSerial),
             'Enter'])
        tmux_send.wait()
        print("[NaBo] Send retry command success ^^")
        logging.info("[NaBo] Send retry command success ^^")
        print('run retry --retry ' + str(timeRetry) + ' --retry-type FAILED ' + str(listSerial))
        logging.info('run retry --retry ' + str(timeRetry) + ' --retry-type FAILED ' + str(listSerial))

if __name__ == '__main__':
    timeToRetry, runtype, ModuleName, ResultPath, echoIp, SSname,CanDevices,Devices = agruments()
    xmltree = ET.parse(ResultPath)
    echoPort = 54689
    Npass = 0
    Nfail = 0
    NmoduleDone = 0
    NmoduleFail = 0
    NmoduleName = ""
    roo = xmltree.getroot()
    path = str(ResultPath)
    for ele in roo.findall('Summary'):
        print("pass=" + ele.get('pass'))
        logging.info("pass=" + ele.get('pass'))
        Npass = ele.get('pass')
        Nfail = ele.get('failed')
        NmoduleDone = ele.get('modules_done')
        NmoduleFail = ele.get('modules_total')
        print("failed=" + ele.get('failed'))
        logging.info("failed=" + ele.get('failed'))
        print("modules_done=" + ele.get('modules_done'))
        logging.info("modules_done=" + ele.get('modules_done'))
        print("modules_total=" + ele.get('modules_total'))
        logging.info("modules_total=" + ele.get('modules_total'))
    List_devices = []
    for temp in Devices.split("_"):
        if not str(temp).__eq__(""):
            List_devices.append(temp)
    if CanDevices is not None and str(ModuleName).__contains__("CtsCarTestCases") and timeToRetry == 0:
        canSerial="-s "+CanDevices
        sendCommand(canSerial, runtype, timeToRetry, SSname)
    else:
        StrSerial = MakeSerialStr(List_devices)
        sendCommand(StrSerial, runtype, timeToRetry, SSname)
