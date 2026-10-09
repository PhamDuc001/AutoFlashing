import serial
import time
from threading import Thread
from .procResponse import *


class serialPort:
    def __init__(self, COMPort):
        self.ATS_SYNC = 0x61
        self.ATS_TAIL_BYTE_LENGTH = 3
        self.ATS_PROTOCOL_CRC_KEY_VALUE = 0xC659
        self.ATS_CMD_ID = 0x10
        self.HEADER_END_BYTE = 0x6F
        self.ATS_TAIL = 0x6F
        self.RXBUFFSIZE = 1024 * 8
        self.ATS_EXCLUDE_BYTE_LENGTH_FIELD = 6  # 6 = StartBit(2) + Length(4)
        self.ATS_LENGTH_BYTE_LENGTH = 4
        self.ATS_HEADER_BYTE_LENGTH = 2
        self.ATS_RX_LEN1_BYTE_INDEX = 2
        self.ATS_RX_LEN2_BYTE_INDEX = 3
        self.ATS_RX_LEN3_BYTE_INDEX = 4
        self.ATS_RX_LEN4_BYTE_INDEX = 5

        self.rxBuff = [0 for _ in range(self.RXBUFFSIZE)]  # 8Kbytes List Initialization
        self.rxBuffHeadPos = 0
        self.rxBuffTailPos = 0
        self.terminate_serial_read_thread = False
        self.terminate_serial_proc_thread = False
        self.readRxThreadInstance = None
        self.procRxThreadInstance = None
        self.initDone = False
        self.isCANFDSupport = False
        self.CANChannel = 0
        self.CANatVersion = ''

        self.proc = procResponse(self)
        self.ser = serial.Serial(
            port=COMPort,  # ex, 'COM10'
            baudrate=115200,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0)
        if self.ser.is_open == True:
            print('{} Connected'.format(self.ser.portstr))
            # Start serial read thread.
            self.terminate_serial_read_thread = False
            self.readRxThreadInstance = Thread(target=self.readRxThread, args=())
            self.readRxThreadInstance.daemon = True
            self.readRxThreadInstance.start()

            # Start serial proc thread
            self.terminate_serial_proc_thread = False
            self.procRxThreadInstance = Thread(target=self.procRxThread, args=())
            self.procRxThreadInstance.daemon = True
            self.procRxThreadInstance.start()

    def closeEvent(self, ev):
        self.terminate_serial_read_thread = True
        self.terminate_serial_proc_thread = True

    def readRxThread(self):
        while self.terminate_serial_read_thread == False:
            # Read a byte from serial port.
            for c in self.ser.read():
                self.rxBuff[self.rxBuffHeadPos] = c
                self.rxBuffHeadPos = (self.rxBuffHeadPos + 1) % self.RXBUFFSIZE

    def getByte(self):
        retVal = 0
        if self.rxBuffHeadPos != self.rxBuffTailPos:
            retVal = self.rxBuff[self.rxBuffTailPos]
            self.rxBuffTailPos = (self.rxBuffTailPos + 1) % self.RXBUFFSIZE
            return True, retVal
        else:
            return False, 0

    def clearRxBuff(self):
        self.rxBuff = [0 for _ in range(self.RXBUFFSIZE)]  # 8Kbytes List Initialization
        self.rxBuffHeadPos = 0
        self.rxBuffTailPos = 0

    def procRxThread(self):
        RedTRecvData = [0 for _ in range(self.RXBUFFSIZE)]  # 8Kbytes List Initialization
        PCCmdRecvStep = 0
        nPacketLen = 0
        cTemp = 0;
        cRecent = 0

        while self.terminate_serial_proc_thread == False:
            retStatus, cTemp = self.getByte()
            if retStatus == True:
                if PCCmdRecvStep == 0 and cTemp == 0x61:
                    PCCmdRecvStep = PCCmdRecvStep + 1
                elif PCCmdRecvStep == 1 and cTemp == 0x61:
                    PCCmdRecvStep = PCCmdRecvStep + 1
                    # print('[I] All Sync Bytes Received!')
                elif PCCmdRecvStep >= 2:
                    if cRecent == 0x61 and cTemp == 0x61:
                        if nPacketLen > 0 and (PCCmdRecvStep < nPacketLen + self.ATS_EXCLUDE_BYTE_LENGTH_FIELD):
                            # Re-Sync is not allowed while parsing on data field.
                            pass
                        else:
                            PCCmdRecvStep = 0
                            nPacketLen = 0
                            RedTRecvData[PCCmdRecvStep] = cRecent;
                            PCCmdRecvStep = PCCmdRecvStep + 1
                            RedTRecvData[PCCmdRecvStep] = cTemp;
                            PCCmdRecvStep = PCCmdRecvStep + 1
                            continue

                    cRecent = cTemp
                    if PCCmdRecvStep < self.RXBUFFSIZE:
                        RedTRecvData[PCCmdRecvStep] = cTemp;
                        PCCmdRecvStep = PCCmdRecvStep + 1
                    else:
                        print('[E] Max Buffer Size Exceeded!')
                        PCCmdRecvStep = 0
                        nPacketLen = 0
                        self.clearRxBuff()

                    if PCCmdRecvStep == self.ATS_EXCLUDE_BYTE_LENGTH_FIELD:
                        nPacketLen = 0
                        nPacketLen = (((RedTRecvData[self.ATS_RX_LEN1_BYTE_INDEX] << 24)) & 0xff000000)
                        nPacketLen |= ((RedTRecvData[self.ATS_RX_LEN2_BYTE_INDEX] << 16) & 0xff0000)
                        nPacketLen |= ((RedTRecvData[self.ATS_RX_LEN3_BYTE_INDEX] << 8) & 0xff00)
                        nPacketLen |= (RedTRecvData[self.ATS_RX_LEN4_BYTE_INDEX] & 0xff)
                    else:
                        if cTemp == 0x6F and PCCmdRecvStep == (nPacketLen + self.ATS_EXCLUDE_BYTE_LENGTH_FIELD):
                            # Valid Data Received!
                            tmpList = list(RedTRecvData[self.ATS_HEADER_BYTE_LENGTH:PCCmdRecvStep])
                            self.procResponse(tmpList, len(tmpList))
                            # Initialize variables to process the next response.
                            PCCmdRecvStep = 0;
                            nPacketLen = 0
                        elif PCCmdRecvStep > (nPacketLen + self.ATS_EXCLUDE_BYTE_LENGTH_FIELD):
                            # print('[E] Invalid Length!')
                            PCCmdRecvStep = 0
                            nPacketLen = 0
                else:
                    # print('[E] Error Step {}'.format(PCCmdRecvStep))
                    PCCmdRecvStep = 0
                    nPacketLen = 0
                    self.clearRxBuff()

            time.sleep(0.001)  # 1msec sleep.

    def calcCRC16(self, buff, len):
        crc16 = 0xFFFF
        for i in range(0, len):
            tmp = (buff[i] & 0xFF) ^ (crc16 & 0x00FF)
            for j in range(0, 8):
                if tmp & 1:
                    tmp = (tmp >> 1) ^ self.ATS_PROTOCOL_CRC_KEY_VALUE
                else:
                    tmp = tmp >> 1
            crc16 = (crc16 >> 8) ^ tmp
        return crc16

    def procResponse(self, pBuffer, nLen):
        nPacketLen = 0;
        nIdx = 0
        nPackLen = pBuffer[nIdx];
        nIdx = nIdx + 1
        nPackLen = (nPackLen << 8) | pBuffer[nIdx];
        nIdx = nIdx + 1
        nPackLen = (nPackLen << 8) | pBuffer[nIdx];
        nIdx = nIdx + 1
        nPackLen = (nPackLen << 8) | pBuffer[nIdx];
        nIdx = nIdx + 1

        nCommandID = pBuffer[nIdx];
        nIdx = nIdx + 1
        if nCommandID == self.ATS_CMD_ID:
            nCommandType = pBuffer[nIdx];
            nIdx = nIdx + 1

            nIdx = nIdx + (nPackLen - self.ATS_TAIL_BYTE_LENGTH - 2)
            nCRC = ((pBuffer[nIdx] << 8) & 0xff00);
            nIdx = nIdx + 1
            nCRC = nCRC | (pBuffer[nIdx] & 0xff);
            nIdx = nIdx + 1

            nTail = pBuffer[nIdx];
            nIdx = nIdx + 1

            crcCalTmp = []
            for i in range(0, nPackLen - self.ATS_TAIL_BYTE_LENGTH):
                crcCalTmp.append(pBuffer[self.ATS_LENGTH_BYTE_LENGTH + i])
            nCalCrc = self.calcCRC16(crcCalTmp, nPackLen - self.ATS_TAIL_BYTE_LENGTH)

            if nCRC == nCalCrc:
                # print('[I] CRC Compared Success!')
                if nTail == self.ATS_TAIL:
                    # print('[I] Valid Command Received!')
                    tmpLst = list(pBuffer[self.ATS_LENGTH_BYTE_LENGTH + 2:len(pBuffer)])
                    self.proc.proc(nCommandType, tmpLst, nPackLen - self.ATS_TAIL_BYTE_LENGTH - 2)
        else:
            print('[W] Unknown Command Received!')

    def procSend(self, buff, len):
        sendBuff = []
        if len > 0 and self.ser.is_open == True:
            sendBuff.append(self.ATS_SYNC)
            sendBuff.append(self.ATS_SYNC)

            sendBuff.append(((len + self.ATS_TAIL_BYTE_LENGTH) >> 24) & 0xFF)
            sendBuff.append(((len + self.ATS_TAIL_BYTE_LENGTH) >> 16) & 0xFF)
            sendBuff.append(((len + self.ATS_TAIL_BYTE_LENGTH) >> 8) & 0xFF)
            sendBuff.append((len + self.ATS_TAIL_BYTE_LENGTH) & 0xFF)

            for i in range(0, len):
                sendBuff.append(buff[i])

            CRC16 = self.calcCRC16(buff, len)
            sendBuff.append((CRC16 >> 8) & 0xFF)
            sendBuff.append(CRC16 & 0xFF)
            sendBuff.append(self.HEADER_END_BYTE)

            # send buff to COM port.
            self.ser.write(bytearray(sendBuff))

    #####################################################################################
    ## Internal Functions
    def setCANatDevLEDNum(self, num):
        cmdBuff = [0x10, 0x31]
        cmdBuff.append(num)
        self.procSend(cmdBuff, len(cmdBuff))

    def getBaudrate(self):
        cmdBuff = [0x10, 0x04]  # CommandID(0x10), GetBaudrate CommandType(0x04)
        self.procSend(cmdBuff, len(cmdBuff))

    def setDeviceNumber(self, devNo):
        cmdBuff = [0x10, 0x09, 0x00]  # CommandID(0x10), SetDeviceNumber CommandType(0x09)
        cmdBuff[2] = devNo
        self.procSend(cmdBuff, len(cmdBuff))

    def setBaudrate(self, nCAN1, nCAN2):
        cmdBuff = [0x10, 0x03, 0x00, 0x00]  # CommandID(0x10), SetBaudrate CommandType(0x03)
        cmdBuff[2] = nCAN1
        cmdBuff[3] = nCAN2
        self.procSend(cmdBuff, len(cmdBuff))
        # Send ReqInitial Command
        self.reqInitial()

    def reqInitial(self):
        cmdBuff = [0x10, 0x01]  # CommandID(0x10), RequestInitial CommandType(0x01)
        self.procSend(cmdBuff, len(cmdBuff))

    def reqVersion(self):
        cmdBuff = [0x10, 0x02]  # CommandID(0x10), RequestVersion CommandType(0x02)
        self.procSend(cmdBuff, len(cmdBuff))

    def sendCANatTerminate(self):
        cmdBuff = [0x10, 0x0A]  # CommandID(0x10), RequestCANatTerminate CommandType(0x0A)
        self.procSend(cmdBuff, len(cmdBuff))

    #####################################################################################
    ## External Functions
    def initCANat(self, isCANFDSupport, CANChan):
        self.initDone = False
        self.CANChannel = CANChan
        self.isCANFDSupport = isCANFDSupport
        self.getBaudrate()  # Send GetBaudrate Command First. After receiving a response to this command, Send SetDeviceNumber command.

    def disConnect(self):
        self.terminate_serial_read_thread = True
        self.terminate_serial_proc_thread = True
        self.sendCANatTerminate()

    def sendCanMessage(self, msgID, cycleTime, msgLen, msgData):
        cmdBuff = [0x10, 0x00]  # CommandID(0x10), CANControl CommandType(0x00)
        cmdBuff.append(0)  # 0xFF : Stop sending message,  Other Values : Send a Message
        cmdBuff.append(int(self.isCANFDSupport))  # 0: Classic CAN, 1: CAN FD
        cmdBuff.append(self.CANChannel)  # CAN Channel 1 or 2

        if cycleTime > 0:
            cmdBuff.append(1)  # 0: Event, 1:Cyclic
        else:
            cmdBuff.append(0)
        cmdBuff.append((cycleTime & 0xFF00) >> 8)  # CycleTime Hi Byte
        cmdBuff.append(cycleTime & 0x00FF)  # CycleTime Lo Byte

        if msgID > 0x7FF:  # Check if this message ID is standard or extended.
            # Extended Address
            cmdBuff.append((msgID >> 24) & 0xFF)
            cmdBuff.append((msgID >> 16) & 0xFF)
            cmdBuff.append((msgID >> 8) & 0xFF)
            cmdBuff.append(msgID & 0xFF)
        else:
            # Standard Address
            cmdBuff.append((msgID & 0xFF00) >> 8)  # Message ID Hi Byte
            cmdBuff.append(msgID & 0x00FF)  # Message ID Lo Byte
            cmdBuff.append(0xFF)  # 0xFFFF means that this address is standard format
            cmdBuff.append(0xFF)  #

        cmdBuff.append(msgLen)  # Message Length
        for i in range(0, msgLen):
            cmdBuff.append(msgData[i])

        self.procSend(cmdBuff, len(cmdBuff))

    def stopCanMessage(self, msgID):
        cmdBuff = [0x10, 0x00]  # CommandID(0x10), CANControl CommandType(0x00)
        cmdBuff.append(0xFF)  # 0xFF : Stop sending message by ID,  Other Values : Send a Message
        cmdBuff.append(int(self.isCANFDSupport))  # 0: Classic CAN, 1: CAN FD
        cmdBuff.append(self.CANChannel)  # CAN Channel 1 or 2

        cmdBuff.append(1)  # 0: Event, 1:Cyclic
        cmdBuff.append(0)  # CycleTime Hi Byte
        cmdBuff.append(0)  # CycleTime Lo Byte

        if msgID > 0x7FF:  # Check if this message ID is standard or extended.
            # Extended Address
            cmdBuff.append((msgID >> 24) & 0xFF)
            cmdBuff.append((msgID >> 16) & 0xFF)
            cmdBuff.append((msgID >> 8) & 0xFF)
            cmdBuff.append(msgID & 0xFF)
        else:
            # Standard Address
            cmdBuff.append((msgID & 0xFF00) >> 8)  # Message ID Hi Byte
            cmdBuff.append(msgID & 0x00FF)  # Message ID Lo Byte
            cmdBuff.append(0xFF)  # 0xFFFF means that this address is standard format
            cmdBuff.append(0xFF)  #

        dummyMsg = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        cmdBuff.append(len(dummyMsg))  # Message Length
        for data in dummyMsg:
            cmdBuff.append(data)

        self.procSend(cmdBuff, len(cmdBuff))