from serialPort import *
from dbcMgr import *
Candbc = os.getcwd()+"/IVI_EXT_CAN.dbc"
ser = serialPort('/dev/canat')
ser.initCANat(True, 1)
dbcFile = Candbc
print(dbcFile)
db = dbcMgr()
if db.parseDBC(dbcFile) == False:
    print('[W] Fail to parse DBC File!')
msgIdHexDict = db.readParsedDBC()
time.sleep(3)
if len(sys.argv[1].split(','))>1:
    while True:
        try:
            for signal in sys.argv[1].split(','):
                messageSplit = signal.split(':')
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
        except KeyboardInterrupt:
            ser.disConnect()
            break
else:
    for signal in sys.argv[1].split(','):
        messageSplit = signal.split(':')
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
db.clearMsg()
ser.disConnect()

