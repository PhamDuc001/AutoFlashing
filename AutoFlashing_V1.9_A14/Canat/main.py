from serialPort import *
from dbcMgr import *
import serial.tools.list_ports as scplist
import json


def printJson(param):
    print(json.dumps(param, indent=4, ensure_ascii=False))
    print('')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("please input dbcfile")
    canatPN = ["STM32 Virtual ComPort"]
    existPort = None
    for port in scplist.comports():
        if port.product is not None and any([canatPNItem in port.product for canatPNItem in canatPN]):
            existPort = port.device
    ser = None
    if existPort:
        ser = serialPort(existPort)
    else:
        print("CANat Not Exist")
        quit()
    count =5
    while count>0:
        ser.initCANat(True,
                  1)
        count-=1# Parameter : CAN FD Support Flag - False(Classic CAN) , True(CAN FD) / CAN Channel Number 1 or 2
        time.sleep(5)

    # dbcFile = os.getcwd() + '/' + sys.argv[1]
    dbcFile = sys.argv[1]
    print(dbcFile)
    db = dbcMgr()
    if db.parseDBC(dbcFile) == False:
        print('[W] Fail to parse DBC File!')
        quit()
    msgIdHexDict = db.readParsedDBC()

    time.sleep(3)
    for item in sys.argv[2:]:
        messageSplit = item.split(':')
        msgID = None
        signalName = None
        value = None
        waitTime = None
        if len(messageSplit) == 3:
            signalName = messageSplit[0]
            value = int(messageSplit[1])
            waitTime = int(messageSplit[2])
            if len(msgIdHexDict[signalName]) > 1:
                raise Exception("signal is duplicated")
            msgID = int(msgIdHexDict[signalName][0], 16)
        elif len(messageSplit) == 4:
            msgID = messageSplit[0]
            signalName = messageSplit[1]
            value = int(messageSplit[2])
            waitTime = int(messageSplit[3])
        else:
            raise Exception("argument is invalid" + str(messageSplit))

        msgID, msgLen, msgCycle, msgData = db.updateSig(msgID, signalName, value)
        ser.sendCanMessage(msgID, msgCycle, msgLen, msgData)
        time.sleep(waitTime)


    # Clear out DBC message data and signal values
    db.clearMsg()
    ser.disConnect()
    # print('[I] Clear out the DBC messages')
    # print('if you want to close CANat, please input ctrl+c')
    # # Close process. Stop all threads.
    # while True:
    #     try:
    #         time.sleep(1)
    #     except KeyboardInterrupt as e:
    #         ser.disConnect()
    #         print('[I] Exit from Main')
    #         break
