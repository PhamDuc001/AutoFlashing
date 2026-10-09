from serialPort import *
from dbcMgr import *
import serial.tools.list_ports as scplist
import json

def printJson(param):
    print(json.dumps(param, indent=4, ensure_ascii = False))
    print('')

if __name__ == "__main__" :
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
        #quit()
        
    ser.initCANat(False, 1) # Parameter : CAN FD Support Flag - False(Classic CAN) , True(CAN FD) / CAN Channel Number 1 or 2

    dbcFile = os.getcwd() + '/' + sys.argv[1]
    db = dbcMgr()
    messageList = db.parseDBC(dbcFile)
    if not messageList:
        print('[W] Fail to parse DBC File!')
        quit()

    time.sleep(3)

    # VechcleSpeed – 100
    msgID, msgLen, msgCycle, msgData = db.updateSig(0x28A, 'VehicleSpeed', 100)
    ser.sendCanMessage(msgID, msgCycle, msgLen, msgData)
    time.sleep(20)
    
    # # ParkingBrakeStatus - 1
    # msgID, msgLen, msgCycle, msgData = db.updateSig(0x451, 'ParkingBrakeStatus', 1)
    # ser.sendCanMessage(msgID, msgCycle, msgLen, msgData)
    # time.sleep(0)
    #
    # # RearGearEngaged - 1
    # msgID, msgLen, msgCycle, msgData = db.updateSig(0x453, 'RearGearEngaged', 1)
    # ser.sendCanMessage(msgID, msgCycle, msgLen, msgData)
    # time.sleep(0)
    #
    # # GearLeverPosition_v2 - 2
    # msgID, msgLen, msgCycle, msgData = db.updateSig(0x12F, 'GearLeverPosition_v2', 2)
    # ser.sendCanMessage(msgID, msgCycle, msgLen, msgData)
    # time.sleep(0)

    # Clear out DBC message data and signal values
    db.clearMsg()
    print('[I] Clear out the DBC messages')
    print('if you want to close CANat, please input ctrl+c')
    # Close process. Stop all threads.
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt as e:
            ser.disConnect()
            print('[I] Exit from Main')
            break
