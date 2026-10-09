import argparse
import glob
import json
import multiprocessing
import os.path
import shutil
import signal
from datetime import time
from time import gmtime
import pandas
from numpy import nan
from ppadb.client import Client
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import threading
import logging
import xml.etree.ElementTree as ET
from Canat.serialPort import *
from Object.devices import devices
from Object.Result import Result
from Object.PlanOb import Plan
from Object.PlanOb import commandline
from openpyxl import Workbook
import concurrent.futures

workspace = None
IPAddr = "10.218.147.60"
portConnect = 54689
try:
    os.mkdir(os.path.join(os.getcwd(), "logs"))
except Exception as e:
    print(e)
try:
    os.mkdir(os.path.join(os.getcwd(), "report"))
except Exception as e:
    print(e)

filenameLog = "AutoRetry_" + str(datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + ".log"
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s [%(pathname)s:%(lineno)d in function %(funcName)s]')

# create file handler
fh = logging.FileHandler(os.getcwd() + "/logs/" + filenameLog)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# create console handler
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
# Create Ecxel report file
workbook = Workbook()
sheet = workbook.active
sheet.append(["Module", "Round", "Pass", "Fail", "Module Pass", "Total Module", "Total Time"])
CanatTestPath = None
# desktopPath = os.environ.get('HOME') + "/GoogleQA"
EnvironmentFol = None
toolType = None
SSID_v6 = None  # line2.split(" ")[0]
PWS_v6 = None  # line2.split(" ")[1]

def sendCanSignal(canSignal):
    global workspace
    global CanatTestPath
    print("Start send CANat Signal {}".format(canSignal))
    try:
        os.chdir(workspace+"/Canat")
        process = subprocess.Popen(
            ["bash", str(CanatTestPath), canSignal],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, )
        process.wait()
    except Exception as e:
        if e.__eq__(KeyboardInterrupt):
            print("Event is set")
            process.send_signal(signal.CTRL_C_EVENT)
        else:
            print(e)

    output, error = process.communicate()
    if not error is None:
        for line in error.decode("utf-8").split("\n"):
            print(line)
    if not output is None:
        for ot in output.decode("utf-8").split("\n"):
            print(ot)


sendCANat = multiprocessing.Process(
    target=sendCanSignal,
    args=("VehicleSpeed:100:0,ParkingBrakeStatus:1:0,RearGearEngaged:1:0,GearLeverPosition_v2:2:0",), )

resetCANat = multiprocessing.Process(
    target=sendCanSignal,
    args=("VehicleSpeed:0:0,ParkingBrakeStatus:0:0,RearGearEngaged:0:0,GearLeverPosition_v2:0:0",), )


def agruments():
    parser = argparse.ArgumentParser(description='parse an XML file')
    parser.add_argument('-t', '--testsuite', help='Test suite')
    parser.add_argument('-v', '--toolver', help='Tool version')
    parser.add_argument('-p', '--plan', help='Path to excel plan file')
    parser.add_argument('-w', '--workspace', help='Path to excel plan file')
    args = parser.parse_args()
    testSuite = str(args.testsuite)
    toolver = str(args.toolver)
    newPath1= str(args.plan).replace("\\", "/")
    newPath1.replace("//", "/")
    newPath2 = str(args.workspace).replace("\\", "/")
    newPath2.replace("//", "/")
    return testSuite,toolver, newPath1, newPath2




class windows():
    def __init__(self):
        super().__init__()
        self.ser = None
        self.module = None
        self.tradefed = None
        self.ReportFolderPath = None
        self.ResultSS = None
        self.LogFolder = None
        self.CtsTradefedPath = None
        self.ResultPath = None
        self.Toolfoldername = None
        self.ModelType = None
        self.testItem = None
        self.tooltype = None
        self.PRE = multiprocessing.Process(target=self.ConnectWIFI)
        self.x = None
        self.countModule = None
        self.version = "Version 1.5"
        self.path = None
        self.ssName = ""
        self.runcommand = None
        self.mRun = ""
        self.desktopPath = os.environ.get('HOME') + "/GoogleQA"
        global workspace, line1, line2
        self.EnvironmentScripts = str(workspace) + "/Environment/scripts"
        global EnvironmentFol
        EnvironmentFol = self.EnvironmentScripts
        try:
            wifiInfo = open(EnvironmentFol + "/wifi.txt", "r")
            line1 = wifiInfo.readline()
            line2 = wifiInfo.readline()
        except Exception as e:
            print(e)
            logger.error(e)
        self.SSID = line1.split(" ")[0]
        self.PWS = line1.split(" ")[1][:-1]
        global SSID_v6
        global PWS_v6
        SSID_v6 = line2.split(" ")[0]
        PWS_v6 = line2.split(" ")[1]
        self.round = 0
        self.listFolder = ['01.Full', '00.Internal', '00.OEM_APFE', '00.OEM_Delivery', '00.Report']
        self.title = "Auto Retry"
        self.adb = Client(host="localhost", port=5037)
        self.filename = None
        self.Plan = []
        self.TotalTime = None
        self.canATisPlug=None
        self.deviceList=[]
        self.currResults=""


    def makePlan(self,OBJ_pl):
        round = []
        self.Plan = []
        for Temp_cmd in OBJ_pl.ListCommand:
            round.append(runRound(Temp_cmd.command, Temp_cmd.typeRun, Temp_cmd.numOfRetry))
        # print("No" + ". " +"Command"+ " " + "Type" + " " +"Retry"+ '\n')
        for ro in round:
            ro.getInforRound()
            if (not ro.timeRetry is float(nan)) and (not ro.command is float(nan)) and (
                    not ro.typeRun is float(nan)):
                print(ro.command + " " + ro.typeRun + " " + ro.timeRetry + '\n')
                if OBJ_pl.testSuite.__eq__("GSI"):
                    self.tradefed = "cts"
                    self.tooltype = "gsi"
                elif OBJ_pl.testSuite.__eq__("STS"):
                    self.tradefed = "sts"
                    self.tooltype = "sts"
                elif OBJ_pl.testSuite.__eq__("VTS"):
                    self.tradefed = "vts"
                    self.tooltype = "vts"
                elif OBJ_pl.testSuite.__eq__("CTS"):
                    self.tradefed = "cts"
                    self.tooltype = "cts"
                elif OBJ_pl.testSuite.__eq__("ATS"):
                    self.tradefed = "ats"
                    self.tooltype = "ats"
                self.Plan.append(ro)
                global toolType
                toolType = self.tooltype

    def clean_folder_oneTime(self):
        logger.info("[NaBo] Clean Report folder")
        if os.path.exists(self.ReportFolderPath):
            for temp in os.listdir(self.ReportFolderPath):
                try:
                    shutil.rmtree(os.path.join(self.ReportFolderPath, temp), ignore_errors=True)
                    logger.info("Remove {} in report folder".format(str(temp)))
                except Exception as e:
                    logger.error(e)
            logger.info("[NaBo] Delete Results folder")
        if os.path.exists(self.ResultPath):
            for temp in os.listdir(self.ResultPath):
                try:
                    shutil.rmtree(os.path.join(self.ResultPath, temp), ignore_errors=True)
                    logger.info("Remove {} in report folder".format(str(temp)))
                except Exception as e:
                    logger.error(e)
            logger.info("[NaBo] Delete Logs folder")
        if os.path.exists(self.LogFolder):
            for temp in os.listdir(self.LogFolder):
                try:
                    shutil.rmtree(os.path.join(self.LogFolder, temp), ignore_errors=True)
                    logger.info("Remove {} in report folder".format(str(temp)))
                except Exception as e:
                    logger.error(e)

    def runPlan(self):
        self.countModule = 1
        # self.hide()
        # try:
        #     self.adb.devices()
        # except Exception as e:
        #     logger.info(e)
        #     print("Please connect adb devices")
        #     logger.info("Please connect adb devices")
        #     sys.exit()
        self.AutoPrecondition()
        self.clean_folder_oneTime()
        for temp in self.Plan:
            self.RePrecondition()
            self.backupResult()
            time.sleep(10)
            self.KillTmux()
            time.sleep(20)
            self.openTmux()
            self.TimeStart = time.time()
            time.sleep(30)
            self.sendCommand(temp.command)
            self.makeModuleFolderReport(temp.command)
            self.retry = int(temp.timeRetry)
            retryNum = 0
            self.TotalTestCasePass = 0
            self.TotalModuleDone = 0
            LogCurr = lastTestResult()
            time.sleep(20)
            self.currResults = LogCurr.getLastTestFolder(self.LogFolder)
            self.currResults = os.path.join(self.ResultPath, self.currResults)
            print('BBBBBBBBBBBBBBBBBBBBBB' + self.currResults)
            os.makedirs(self.currResults, exist_ok=True) 
            watch = OnMyWatch(int(retryNum), temp.typeRun, self.retry, self.ResultPath, self.module,
                              self.TotalTestCasePass, self.TotalModuleDone, self.TimeStart, self.ssName, self.PRE,self.deviceList,self.currResults)
            watch.run()
            print("[NaBo] Finish plan {}".format(temp.command))
            self.countModule += 1
            logger.info("[NaBo] Finish plan {}".format(temp.command))
        self.KillAutoPrecondition()
        # global workspace
        # workbook.save(workspace + "/report/Report_" + str(datetime.now().strftime("%Y.%m.%d_%H.%M.%S")) + ".xlsx")

    def setModuleName(self, name, testItem):
        self.name = name
        self.TestItem = testItem
        self.name = "{:02d}".format(self.countModule) + '.' + self.name
        # self.countModule += 1
        return self.name

    def getDeviceInfo(self):
        logger.info("Start auto detect devices " + self.tooltype)
        list = []
        adb = Client(host="localhost", port=5037)
        for dev in adb.devices():
            tempD = devices()
            tempD.fingerprint = dev.shell("getprop ro.system.build.fingerprint")
            logger.info("Devices " + dev.serial + " fingerprint: {}".format(tempD.fingerprint))
            strT = dev.shell("getprop ro.boot.vbmeta.device_state")
            logger.info("Devices " + dev.serial + " state: {}".format(strT))
            rootStatus = dev.shell("getprop ro.debuggable")
            logger.info("Devices " + dev.serial + " root Status: {}".format(rootStatus))
            tempD.serial = dev.serial
            if str(self.tooltype).__contains__("sts") and str(tempD.fingerprint).__contains__("userdebug") and str(
                    strT).__contains__(
                "locked"):
                tempD.typeOfDevices = "STS"
                logger.info("Devices " + dev.serial + " is : {} device".format(tempD.typeOfDevices))
                if len(list) > 0:
                    if list[0].fingerprint == tempD.fingerprint:
                        list.append(tempD)
                else:
                    list.append(tempD)
            elif (str(self.tooltype).__contains__("cts") or str(self.tooltype).__contains__("ats")) and not str(
                    tempD.fingerprint).__contains__(
                "userdebug") and not str(
                tempD.fingerprint).__contains__("gsi") and not str(strT).__contains__("unlocked"):
                tempD.typeOfDevices = "CTS"
                logger.info("Devices " + dev.serial + " is : {} device".format(tempD.typeOfDevices))
                if len(list) > 0:
                    if list[0].fingerprint == tempD.fingerprint:
                        list.append(tempD)
                else:
                    list.append(tempD)
            elif str(self.tooltype).__contains__("gsi") and str(tempD.fingerprint).__contains__("gsi") and str(
                    rootStatus).__contains__("0") and str(strT).__contains__("unlocked"):
                tempD.typeOfDevices = "GSI"
                logger.info("Devices " + dev.serial + " is : {} device".format(tempD.typeOfDevices))
                if len(list) > 0:
                    if list[0].fingerprint == tempD.fingerprint:
                        list.append(tempD)
                else:
                    list.append(tempD)
            elif str(self.tooltype).__contains__("vts") and str(tempD.fingerprint).__contains__("gsi") and str(
                    rootStatus).__contains__("1") and str(strT).__contains__("unlocked"):
                tempD.typeOfDevices = "VTS"
                logger.info("Devices " + dev.serial + " is : {} device".format(tempD.typeOfDevices))
                if len(list) > 0:
                    if list[0].fingerprint == tempD.fingerprint:
                        list.append(tempD)
                else:
                    list.append(tempD)
        return list

    def Precondition_IPV6(self):
        global SSID_v6, PWS_v6,EnvironmentFol
        for devices in self.deviceList:
            logger.info("Precondition setting for " + devices)
            print("Precondition setting for ", devices)
            os.chdir(EnvironmentFol)
            subprocess.Popen(
                ['bash', os.environ.get('HOME') + "/Environment/scripts" + '/Precondition.sh', devices, SSID_v6,
                 PWS_v6])

    def makeModuleFolderReport(self, RunCommand):
        logger.info("Start make folder Report")
        self.testItem = str(RunCommand).split(" ")[1]
        if len(str(RunCommand).split(" ")) > 3:
            self.module = str(RunCommand).split(" ")[3]
        if str(self.tooltype).__eq__("sts"):
            self.module = "00. "
            logger.info("Start make folder {}".format(self.module))
        elif str(RunCommand).split(" ")[2].__contains__("filter"):
            self.module = "00.Multiple"
            logger.info("Start make folder {}".format(self.module))
        if not self.module.__eq__("00.Multiple"):
            self.module = "{:02d}".format(self.countModule) + '.' + self.module
            logger.info("Start make folder {}".format(self.module))
        try:
            self.moduleFolderReport = os.path.join(str(self.ReportFolderPath), str(self.module))
            if not os.path.exists(self.moduleFolderReport):
                os.mkdir(self.moduleFolderReport)
        except FileExistsError:
            print("Folder Already Exist")
            logger.info("Folder " + self.moduleFolderReport + " Already Exist")
        try:
            self.moduleResultReport = os.path.join(self.moduleFolderReport, "results")
            os.mkdir(self.moduleResultReport)
        except FileExistsError:
            logger.info("Folder " + self.moduleResultReport + " Already Exist")
            print("Folder Already Exist")
        try:
            self.moduleLogReport = os.path.join(self.moduleFolderReport, "logs")
            os.mkdir(self.moduleLogReport)
        except FileExistsError:
            logger.info("Folder " + self.moduleLogReport + " Already Exist")
            print("Folder Already Exist")

    def sendCommand(self, command):
        self.command = command
        if len(self.deviceList) == 0:
            logger.error("Not exsist device ")
            sys.exit()
        temp = ""
        number_devices = len(self.deviceList)
        for ser in self.deviceList:
            temp += ("-s " + str(ser) + " ")
        subprocess.Popen(['tmux', 'send-keys', '-t', self.ssName, self.runcommand, 'Enter'])
        time.sleep(15) 
        subprocess.Popen(['tmux', 'send-keys', '-t', self.ssName, self.command + " --shard-count " + str(number_devices) + " " + temp, 'Enter'])
        print("Running xts with command " + self.runcommand + " " + self.command + " --shard-count " + str(
            number_devices) + " " + temp)
        logger.info("Running xts with command " + self.runcommand + " " + self.command + " --shard-count " + str(
            number_devices) + " " + temp)


    def folder(self,tempRo):
        if tempRo.testSuite.__eq__("GSI"):
            self.tradefed = "cts"
            self.tooltype = "gsi"
        elif tempRo.testSuite.__eq__("STS"):
            self.tradefed = "sts"
            self.tooltype = "sts"
        elif tempRo.testSuite.__eq__("VTS"):
            self.tradefed = "vts"
            self.tooltype = "vts"
        elif tempRo.testSuite.__eq__("CTS"):
            self.tradefed = "cts"
            self.tooltype = "cts"
        elif tempRo.testSuite.__eq__("ATS"):
            self.tradefed = "ats"
            self.tooltype = "ats"
        self.TestSuite = tempRo.testSuite
        self.Toolfoldername=tempRo.toolPath
        self.ResultPath = self.Toolfoldername + "/results/"
        self.CtsTradefedPath = self.Toolfoldername + "/tools"
        self.runcommand = self.Toolfoldername + "/tools/" + self.tradefed + "-tradefed"
        self.ssName = "NaBo_" + tempRo.PlanName
        self.LogFolder = self.Toolfoldername + "/logs/"
        self.path = self.Toolfoldername + "/"
        self.ResultSS = 0
        self.ReportFolderPath = self.path + "/Report"
        print(
            self.ResultPath + "\n" + self.Toolfoldername + "\n" + self.CtsTradefedPath + "\n" + self.runcommand + "\n" + self.LogFolder + "\n" + self.ReportFolderPath)
        logger.info(
            self.ResultPath + "\n" + self.Toolfoldername + "\n" + self.CtsTradefedPath + "\n" + self.runcommand + "\n" + self.LogFolder + "\n" + self.ReportFolderPath)
        try:
            os.mkdir(self.ReportFolderPath)
            logger.info("[NABO] Created report folder")
            print("[NABO] Created report folder")
        except Exception as e:
            logger.error(e)
            print("Folder Report Already Exist")
        try:
            os.mkdir(self.LogFolder)
            logger.info("[NABO] Created logs folder")
            print("[NABO] Created logs folder")
        except Exception as e:
            logger.error(e)
            print("Folder Report Already Exist")
        try:
            os.mkdir(self.ResultPath)
            logger.info("[NABO] Created results folder")
            print("[NABO] Created results folder")
        except Exception as e:
            logger.error(e)
            print("Folder Report Already Exist")
        # self.ReportFolderGenerator()
        self.KillTmux()
        self.openTmux()

    def ReportFolderGenerator(self):
        for direct in self.listFolder:
            try:
                os.mkdir(os.path.join(self.ReportFolderPath, direct))
            except Exception as e:
                logger.error(e)
                print("Folder", direct, " Already Exist")
            parentPath = os.path.join(self.ReportFolderPath, direct)

    def backupResult(self):
        self.resultBackupPath = self.path + "/resultBackup"
        try:
            os.mkdir(self.resultBackupPath)
            print("[NABO] Created results backup folder")
            # os.mkdir(self.logBackupPath)
        except Exception as e:
            logger.error(e)
            print("[NABO] Folder Already Exist")
        if os.path.exists(self.ResultPath):
            for dir in os.listdir(self.ResultPath):
                    run_script(["mv","-f",str(os.path.join(self.ResultPath,dir)), self.resultBackupPath])
        run_script(["rm", "-r", self.ResultPath+"/*"])

    def makeReport(self):
        for dir in os.listdir(self.ResultPath):
            tempPath = os.path.join(self.ResultPath, dir)
            if os.path.isdir(tempPath):
                try:
                    tempdes = os.path.join(self.moduleResultReport, dir)
                    shutil.copytree(tempPath, tempdes)
                except Exception as e:
                    logger.error(e)
                    print("[NaBo] Folder " + dir + " Already Exist In Result Backup")
                    # shutil.rmtree(self.ResultPath + dir, ignore_errors=True)
                    # print("[NaBo] Removed " + dir)
            elif os.path.isfile(tempPath):
                try:
                    shutil.copy2(tempPath, self.moduleResultReport)
                except Exception as e:
                    logger.error(e)
        for dir in os.listdir(self.LogFolder):
            templogPath = os.path.join(self.LogFolder, dir)
            if os.path.isdir(templogPath):
                try:
                    tempdeslog = os.path.join(self.moduleLogReport, dir)
                    shutil.copytree(templogPath, tempdeslog)
                except Exception as e:
                    logger.error(e)
                    print("[NaBo] Folder " + dir + " Already Exist In Log Backup")
            else:
                try:
                    shutil.copy2(templogPath, self.moduleLogReport)
                except Exception as e:
                    logger.error(e)

    def openTmux(self):
        tmux_newSS = subprocess.Popen(['byobu-tmux', 'new-session', '-d', '-s', self.ssName])
        tmux_newSS.wait()
        logger.info("Open new session byobu - Please typing byobu and choose " + self.ssName + " session to view")
        print("Open new session byobu - Please typing byobu and choose " + self.ssName + " session to view")

    def commandGen(self, commandLine):
        self.commandLine = str(commandLine)
        return commandLine.split(" ")

    def RePrecondition(self):
        global EnvironmentFol
        for dev in self.deviceList:
            logger.info("Precondition setting for " + dev)
            print("Precondition setting for ", dev)
            try:
                os.chdir(EnvironmentFol)
                subprocess.Popen(
                ['bash', EnvironmentFol + '/Precondition.sh', dev, self.SSID, self.PWS])
            except Exception as e:
                print(e)

    def ConnectWIFI(self):
        global EnvironmentFol
        while True:
            logger.info("Re-Connect WIFI............")
            print("Re-Connect WIFI............")
            for dev in self.deviceList:
                try:
                    os.chdir(EnvironmentFol)
                    subprocess.Popen(
                        ['bash', EnvironmentFol + '/connectWF.sh', dev, self.SSID, self.PWS])
                except Exception as e:
                    logger.error(e + 'connect wifi')
                    logger.log(e)     
            time.sleep(1800)

    def GetModelInfo(self):
        self.ModelType = ""
        try:
            self.device = self.adb.devices()
        except Exception as e:
            print(e)
            logger.info(e)
        try:
            var = str(self.device[0].shell("getprop ro.build.fingerprint")).split("/")[4]
        except Exception as e:
            print(e)
            logger.info(e)
        if var.split(".")[0] == "ANT":
            self.ModelType = "ACCESS"
        else:
            self.ModelType = "NISSAN"
        return self.ModelType

    def AutoPrecondition(self):
        self.PRE.start()

    def KillAutoPrecondition(self):
        if self.PRE.is_alive():
            self.PRE.kill()
            logger.info("Stop Thread Auto Precondition")

    def KillTmux(self):
        tmux_newSS = subprocess.Popen(['byobu-tmux', 'kill-session', '-t', self.ssName])
        tmux_newSS.wait()
        logger.info("Kill session byobu " + self.ssName)
        print("Kill session byobu " + self.ssName)

    def runThreat(self, ip):
        # self.wathDirect = filedialog.askdirectory(initialdir=desktopPath, title="Select folder")
        self.ServerIp.insert("1.0", self.wathDirect)
        self.ip = ip
        self.watch = watchDog(self.wathDirect, self.ip)
        self.watch.run()

    def startThreat(self):
        file1 = open("ip.txt", "r+")
        ip = file1.read()
        print(ip)
        logger.info("Start listening results")
        print("Start listening results")
        self.x = threading.Thread(target=self.runThreat, args=(ip,))
        self.x.start()

    def stopThreat(self):
        logger.info("stop.listening results")
        print("stop.listening results")
        self.watch.kill()
        self.x.join()


class runRound:
    def __init__(self, command, typeRun, timeRetry):
        self.command = command
        self.timeRetry = timeRetry
        self.typeRun = typeRun

    def getInforRound(self):
        logger.info(self.command + " " + self.typeRun + " " + self.timeRetry)
        print(self.command, " ", self.typeRun, " ", self.timeRetry)


class OnMyWatch:
    # Set the directory on watch
    def __init__(self, retryN, retryType, retry, pathNeedWatch, moduleName, TotalTestCaseFail, TotalModuleDone,
                 TimeStart, ssNAme, Auto_connectWF_thread,device_list,currResult):
        self.observer = Observer()
        self.retryN = retryN
        self.retryType = retryType
        self.retry = retry
        self.pathNeedWatch = pathNeedWatch
        self.moduleName = moduleName
        self.TotalTestCaseFail = TotalTestCaseFail
        self.TotalModuleDone = TotalModuleDone
        self.TimeStart = TimeStart
        self.ssName = ssNAme
        self.PRE = Auto_connectWF_thread
        self.device_list=device_list
        self.currResults=currResult

    def checkLastTimeModify(self,direct):
        tempdir = direct + "/proto"
        iles_path = os.path.join(tempdir, '*')
        files = sorted(glob.iglob(iles_path), key=os.path.getctime, reverse=True)
        timeOj = gmtime(time.time() - os.path.getmtime(files[0]))
        return timeOj

    def run(self):
        event_handler = Listen(self.retryN, self.retry, self.retryType, self.moduleName, self.TotalTestCaseFail,
                               self.TotalModuleDone, self.TimeStart, self.ssName, self.PRE,self.device_list)
                               
        print(f"retryN: {self.retryN}, retry: {self.retry}, retryType: {self.retryType}, moduleName: {self.moduleName}, "
        f"TotalTestCaseFail: {self.TotalTestCaseFail}, TotalModuleDone: {self.TotalModuleDone}, "
        f"TimeStart: {self.TimeStart}, ssName: {self.ssName}, PRE: {self.PRE}, device_list: {self.device_list}")
        
        self.observer.schedule(event_handler, self.pathNeedWatch, recursive=True)
        self.observer.start()
        try:
            while True:
                print('WHILE')
                time.sleep(60)
                logger.info("Listening Result File On {} .....".format(self.pathNeedWatch))
                print("Listening Result File On {} .....".format(self.pathNeedWatch))
              # tempTime = self.checkLastTimeModify(self.currResults)
              # if tempTime.tm_min == 0 and tempTime.tm_hour == 5 :
              #     for temp in self.device_list:
              #         run_script(["adb","-s",temp,"reboot"])
                if event_handler.retryN > self.retry:
                    print("Finish listening zip File on {}".format(self.pathNeedWatch))
                    logger.info("Finish listening zip File on {}".format(self.pathNeedWatch))
                    # try:
                    #     if sendCANat.is_alive():
                    #         sendCANat.kill()
                    #         print("Kill sendCANat function")
                    #         serialPort("/dev/canat").disConnect()
                    # except Exception as e:
                    #     print(e)
                    # try:
                    #     if not resetCANat.is_alive():
                    #         resetCANat.start()
                    # except Exception as e:
                    #     print(e)
                    #     time.sleep(10)
                    # try:
                    #     if resetCANat.is_alive():
                    #         resetCANat.kill()
                    #         print("Kill sendCANat function")
                    #         serialPort("/dev/canat").disConnect()
                    # except Exception as e:
                    #     print(e)
                    self.observer.stop()
                    break
        except Exception as e:
            print(e)
            self.observer.stop()
            logger.info("Observer Stopped")
            print("Observer Stopped")

        self.observer.join()


class watchDog:
    def __init__(self, direct, ipServer):
        self.observer = Observer()
        self.direct = direct
        self.ipServer = ipServer

    def run(self):
        event_handler = FileHandler(self.ipServer)
        self.observer.schedule(event_handler, self.direct, recursive=True)
        self.observer.start()
        try:
            time.sleep(20)
            logger.info("Listening Result File .....")
            print("Listening Result File .....")
        except Exception as e:
            logger.error(e)
            self.observer.stop()
            print("Observer Stopped")
        self.observer.join()

    def kill(self):
        self.observer.stop()


class FileHandler(FileSystemEventHandler):
    def __init__(self, ipServer):
        self.ipServer = ipServer

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(".zip"):
            subprocess.Popen(
                ['python3', 'PushNotification.py', '-msg', "Finished Round !!!", '-ip', self.ipServer, '-p', "54689"])


class Listen(FileSystemEventHandler):
    def __init__(self, retryN, totalRetry, retryType, moduleName, TotalTestCaseFail, TotalModuleDone, TimeStart,
                 sessionName, Auto_connectWF_thread, devices_list):
        self.ser = None
        self.ssName = sessionName
        self.retryN = retryN
        self.retryType = retryType
        self.moduleName = moduleName
        self.TotalTestCaseFail = TotalTestCaseFail
        self.TotalModuleDone = TotalModuleDone
        self.totalRetry = totalRetry
        self.resultOJ = Result()
        self.TimeStart = TimeStart
        self.CANatDevices = None
        self.checkCanAT = False
        self.PRE = Auto_connectWF_thread
        self.devices_list=devices_list

    def ExcelReportGenerator(self):
        logger.info("Start generated excel report")
        sheet.append([self.resultOJ.module, self.resultOJ.round, self.resultOJ.Pass, self.resultOJ.Fail,
                      self.resultOJ.ModulePass, self.resultOJ.TotalModule, self.resultOJ.TotalTime])

    def on_created(self, event):
        adb = Client(host="localhost", port=5037)
        def resetWF():
            global EnvironmentFol
            logger.info("Forget wifi connection")
            print("Forget wifi connection")
            for dev in self.devices_list:
                try:
                    os.chdir(EnvironmentFol)
                    p = subprocess.Popen(
                        ['bash', EnvironmentFol + '/resetWF.sh', dev])
                    p.wait()
                except Exception as e:
                    logger.error(e)
                    logger.log(e)

        def ConnectWF(SSID, PWS):
            global EnvironmentFol
            logger.info("Re-Connect WIFI IPV6 " + SSID)
            print("Re-Connect WIFI IPV6 " + SSID)
            for dev in self.devices_list:
                try:
                    os.chdir(EnvironmentFol)
                    p = subprocess.Popen(
                        ['bash', EnvironmentFol + '/connectWF.sh', dev, SSID, PWS])
                    p.wait()
                except Exception as e:
                    logger.error(e)
                    logger.log(e)

        def run_adb_command(command):
            global workspace
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.wait()
            output, error = process.communicate()
            if not error is None:
                for line in error.decode("utf-8").split("\n"):
                    print(line)
            if not output is None:
                for ot in output.decode("utf-8").split("\n"):
                    print(ot)
            return output.decode("utf-8")

        if event.is_directory:
            return
        if event.src_path.endswith(".zip"):
            timeEnd = time.time()
            logger.info("New Result  has just been generated - % s." % event.src_path)
            print("Ket qua vua dc tao - % s." % event.src_path)
            time.sleep(1)
            Npass = None
            Nfail = None
            NmoduleDone = None
            NmoduleFail = None
            ti = str(event.src_path)
            folderXml = ti[0:len(ti) - 4]
            folder_proto = folderXml + "/proto/"
            xmltree = ET.parse(folderXml + '/test_result.xml')
            roo = xmltree.getroot()
            for ele in roo.findall('Summary'):
                # print("pass=" + ele.get('pass'))
                Npass = int(ele.get('pass'))
                Nfail = int(ele.get('failed'))
                NmoduleDone = int(ele.get('modules_done'))
                NmoduleFail = int(ele.get('modules_total'))
            timeOj = gmtime(timeEnd - self.TimeStart)
            totalTime = time.strftime("%H:%M:%S", timeOj)
            self.resultOJ.module = self.moduleName
            self.resultOJ.round = self.retryN
            self.resultOJ.Pass = Npass
            self.resultOJ.Fail = Nfail
            self.resultOJ.ModulePass = NmoduleDone
            self.resultOJ.TotalModule = NmoduleFail
            self.resultOJ.TotalTime = totalTime
            self.ExcelReportGenerator()
            device_string = ""
            for temp in self.devices_list:
                device_string = device_string + temp + "_"
            try:
                os.chdir(workspace)
            except Exception as e:
                logger.error(e)
                logger.info(e)
            try:
                subprocess.Popen(
                    ['python3', 'Controller/MakeReportFolder.py', '-p', folderXml + '/test_result.xml', '-m', self.moduleName])
            except Exception as e:
                logger.error(e)
                logger.info(e)
            if not os.path.exists(folder_proto) or not os.path.exists(folder_proto + "test-record.pb"):
                self.retryN = self.totalRetry + 1
                logger.error("Not exist test-record -> Skip test for " + self.moduleName)
            elif self.retryN == 0:
                self.TotalTestCaseFail = Nfail
                self.TotalModuleDone = NmoduleFail - NmoduleDone
                if Nfail == 0 and self.TotalModuleDone == 0 and NmoduleDone != 0 and NmoduleFail != 0:
                    self.retryN = self.totalRetry + 1
                else:
                    self.TimeStart = time.time()
                    try:
                        if str(self.moduleName).__contains__("CtsCarTestCases") and (
                                str(self.ssName).__contains__("cts") or str(self.ssName).__contains__("ats")) and os.path.exists("/dev/canat"):
                            count = 10
                            while self.CANatDevices is None:
                                try:
                                    sendCanSignal("VehicleStates:2:0")
                                except Exception as e:
                                    print(e)
                                # Check CANat devices
                                for dev in adb.devices():
                                    run_adb_command("adb -s {} uninstall com.lgedv.checkcanat".format(dev.serial))
                                    time.sleep(5)
                                    run_adb_command(
                                        "adb -s {} uninstall com.lgedv.checkcanat.test".format(dev.serial))
                                    time.sleep(5)
                                    run_adb_command("adb -s {} install -r -g -t {}/checkCanat.apk".format(dev.serial,workspace+"/Environment/scripts"))
                                    time.sleep(5)
                                    run_adb_command(
                                        "adb -s {} install -r -g -t {}/checkCanat-androidTest.apk".format(dev.serial,workspace+"/Environment/scripts"))
                                    time.sleep(5)
                                    try:
                                        line = run_adb_command(
                                            "adb -s {} shell am instrument -w -e class 'com.lgedv.checkcanat.ExampleInstrumentedTest"
                                            "#AutoDetect' "
                                            "com.lgedv.checkcanat.test/androidx.test.runner.AndroidJUnitRunner".format(
                                                dev.serial))
                                        count -= 1
                                    except Exception as e:
                                        logger.error(e)
                                    if line.__contains__("NADUBO_Detected"):
                                        self.CANatDevices = dev.serial
                                        sendCanSignal("VehicleStates:0:0")
                                        break
                                if count == 0:
                                    break
                                time.sleep(10)
                            try:
                                if sendCANat.is_alive():
                                    sendCANat.kill()
                                    time.sleep(10)
                                serialPort("/dev/canat").disConnect()
                                time.sleep(5)
                            except Exception as e:
                                print(e)
                            try:
                                sendCANat.start()
                            except Exception as e:
                                print(e)

                        elif str(self.moduleName).__contains__("CtsLibcoreTestCases") or str(
                                self.moduleName).__contains__("CtsNetTestCases"):
                            if self.PRE.is_alive():
                                self.PRE.kill()
                            time.sleep(5)
                            resetWF()
                            global SSID_v6, PWS_v6
                            ConnectWF(SSID_v6, PWS_v6)
                        try:
                            os.chdir(workspace)
                            if self.CANatDevices is None:
                                subprocess.Popen(
                                    ['python3', 'Retry.py', '-p', folderXml + '/test_result.xml', '-t',
                                     str(self.retryType),
                                     '-r', str(self.retryN), '-ip', str(IPAddr), '-m', self.moduleName, '-s', self.ssName,'-list',device_string])
                            else:
                                subprocess.Popen(
                                    ['python3', 'Retry.py', '-p', folderXml + '/test_result.xml', '-t',
                                     str(self.retryType),
                                     '-r', str(self.retryN), '-ip', str(IPAddr), '-m', self.moduleName, '-s',
                                     self.ssName,
                                     '-can', str(self.CANatDevices),'-list',device_string])
                        except Exception as e:
                            logger.error(e)
                    except KeyError as e:
                        logger.error(e)
                    self.retryN += 1
            else:
                try:
                    serialPort("/dev/canat").disConnect()
                except Exception as e:
                    print(e)
                if sendCANat.is_alive():
                    try:
                        sendCANat.kill()
                        time.sleep(5)
                    except Exception as e:
                        print(e)
                    try:
                        serialPort("/dev/canat").disConnect()
                    except Exception as e:
                        print(e)
                    time.sleep(5)
                if not resetCANat.is_alive():
                    try:
                        resetCANat.start()
                        time.sleep(10)
                    except Exception as e:
                        print(e)
                if resetCANat.is_alive():
                    try:
                        resetCANat.kill()
                        time.sleep(5)
                        serialPort("/dev/canat").disConnect()
                        time.sleep(5)
                    except Exception as e:
                        print(e)
                if self.TotalTestCaseFail == Nfail or self.TotalTestCaseFail < Nfail or Nfail == 0:
                    self.retryN = self.totalRetry + 1
                else:
                    self.TimeStart = time.time()
                    try:
                        os.chdir(workspace)
                        subprocess.Popen(
                            ['python3', 'Retry.py', '-p', folderXml + '/test_result.xml', '-t',
                             str(self.retryType),
                             '-r', str(self.retryN), '-ip', str(IPAddr), '-m', self.moduleName, '-s', self.ssName,'-list',device_string])
                    except Exception as e:
                        logger.error(e)
                    self.retryN += 1

class lastTestResult():
    def __init__(self):
        self.fol_name = None
        self.datetime_oj = None
        self.sorted_fol = None
        self.masterPath = None
        self.folder_unsort = None

    def get_datetime_folder_name(self, fol_name):
        self.fol_name = fol_name
        try:
            main_part = self.fol_name.split("_")[0] + "_" + ".".join(self.fol_name.split("_")[1].split(".")[:3])
            self.datetime_oj = datetime.strptime(main_part, "%Y.%m.%d_%H.%M.%S")
        except Exception as e:
            print(e)
        return self.datetime_oj

    def sortFolder(self, path):
        self.masterPath = path
        self.folder_unsort = [folder for folder in os.listdir(path) 
                          if os.path.isdir(os.path.join(path, folder)) and folder != "latest"]
        self.sorted_fol = sorted(self.folder_unsort, key=self.get_datetime_folder_name)
        return self.sorted_fol


    def getLastTestFolder(self, path):
        folder_list = os.listdir(path)
        print(f"DEBUG: folder_list = {folder_list}")

        if folder_list:
          sorted_list = self.sortFolder(path)
          print(f"DEBUG: sorted_list = {sorted_list}")

          if sorted_list:  # Kiểm tra danh sách đã sắp xếp
            return sorted_list[-1]
          else:
            print("ERROR: sorted_list is empty despite non-empty folder list!")
            return "0"
        else:
            print(f"Folder {path} empty")
            return "0"


def run_script(path):
    print("Start run command: [{}]".format(path))
    logger.info("Start run command: [{}]".format(path))
    p1 = subprocess.Popen(path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,universal_newlines=True)
    for line in p1.stdout:
        print(line,end=' ')
    p1.wait()
    print("Complete command: [{}]".format(path))
    logger.info("Complete command: [{}]".format(path))
def makeFolderTest(toolFol,toolFile):
    try:
        os.mkdir("{}/GoogleQA/TestFolder/{}".format(get_user_home(),toolFol))
    except Exception as e:
        print(e)
        logger.error(e)
    testingFolder = "{}/GoogleQA/TestFolder/{}".format(get_user_home(),toolFol)
    if os.path.isfile(toolFile):
        logger.info("Start extract tool file: {}".format(toolFile))
        run_script(["unzip",toolFile, "-d", testingFolder])
    else:
        print("File {} not Exists".format(toolFile))
        logger.error("File {} not Exists".format(toolFile))
    for dir in os.listdir(testingFolder):
        if dir.__contains__("android"):
            pathTotool = os.path.join(testingFolder, dir)
            return pathTotool
def get_user_home():
  """Returns the user's home directory path."""
  home_dir = os.path.expanduser("~")
  return home_dir
def analysis_plan(filename):
    if filename:
        try:
            filename = r"{}".format(filename)
            df = pandas.read_excel(filename, sheet_name="Sheet1", header=0,
                                   converters={'RunCommand': str, 'TestSuite': str, 'ToolVer': str, 'Serial': str,
                                               'Runtype': str, 'NumberOfRetry': str})
            hashPlan = {}
            f = open('Environment/scripts/tool_define_struct.json')
            data = json.load(f)
            for index, row in df.iterrows():
                cmd = commandline(row[0],row[5],row[4])
                toolFile = str(data[row[1]]).format(row[2])
                nameFolder = row[1]+"_"+row[3]
                if hashPlan.__contains__(nameFolder):
                    hashPlan[nameFolder].ListCommand.append(cmd)
                elif not hashPlan.__contains__(nameFolder):
                    toolPATH = makeFolderTest(nameFolder, toolFile)
                    hashPlan.__setitem__(nameFolder, Plan(nameFolder, row[3], row[1], toolPATH, cmd))

            return hashPlan

        except ValueError:
            logger.error("Plan File could not be opened")
            print("Plan File could not be opened")
        except FileNotFoundError:
            logger.error("Plan Excel File Not Found")
            print("Plan Excel File Not Found")
def main_thread(tempRo):
    tess = windows()
    print("""
             █████╗ ██╗   ██╗████████╗ ██████╗     ██████╗ ███████╗████████╗██████╗ ██╗   ██╗
            ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗    ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗╚██╗ ██╔╝
            ███████║██║   ██║   ██║   ██║   ██║    ██████╔╝█████╗     ██║   ██████╔╝ ╚████╔╝
            ██╔══██║██║   ██║   ██║   ██║   ██║    ██╔══██╗██╔══╝     ██║   ██╔══██╗  ╚██╔╝
            ██║  ██║╚██████╔╝   ██║   ╚██████╔╝    ██║  ██║███████╗   ██║   ██║  ██║   ██║
            ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝   VERSION 1.8

            """)
    tess.__init__()
    try:
        check = serialPort("/dev/canat")
        sendCanSignal()
        if check: tess.canATisPlug = True
    except Exception as e:
        print("Canat not exist")
        tess.canATisPlug = False
    tess.Toolfoldername = tempRo.toolPath
    for dv in tempRo.serial.split(","):
        tess.deviceList.append(dv)
    tess.makePlan(tempRo)
    tess.folder(tempRo)
    tess.runPlan()
    print("""
            ███████╗██╗███╗   ██╗██╗███████╗██╗  ██╗
            ██╔════╝██║████╗  ██║██║██╔════╝██║  ██║
            █████╗  ██║██╔██╗ ██║██║███████╗███████║
            ██╔══╝  ██║██║╚██╗██║██║╚════██║██╔══██║
            ██║     ██║██║ ╚████║██║███████║██║  ██║
            ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝╚══════╝╚═╝  ╚═╝

            """)
if __name__ == '__main__':
    try:
        testsuite,toolVersion, pathToPlan, workspace = agruments()
        home_direct=get_user_home()
        CanatTestPath= workspace + "/Canat/can.sh"
        try:
            run_script(["rm", "-r", "{}/GoogleQA/TestFolder".format(home_direct)])
        except Exception as e:
            print(e)
            logger.error(e)
        try:
            os.mkdir("{}/GoogleQA/TestFolder".format(home_direct))
        except Exception as e:
            print(e)
            logger.error(e)
        list_of_plan = analysis_plan(pathToPlan)
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=6)
        for tempRound in list_of_plan:
            temp = list_of_plan.get(tempRound)
            #main_thread(temp)
            pool.submit(main_thread,(temp))

        print("Main thread continuing to run")

    except KeyboardInterrupt:
        sys.exit()
