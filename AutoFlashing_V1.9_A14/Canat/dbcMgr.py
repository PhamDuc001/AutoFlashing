import sys
import re
import os
from os import walk
import ast

import time
import operator


class Signal:

    def __init__(self):
        self.name = ""
        self.startBit = -1
        self.bitSize = -1
        self.byteOrder = ""
        self.factor = -1
        self.offset = -1
        self.unit = ""
        self.max = -1
        self.min = -1
        self.receivers = []
        self.valueDesc = {}
        self.comment = ""
        self.msgInfo = []
        self.value = 0
    def getName(self):
        return self.name

class Message:

    def __init__(self):
        self.id = -1
        self.HEXIDstr = ""
        self.len = -1
        self.name = ""
        self.emitter = ""
        self.period = 0
        self.type = ""
        self.byteOrderStr = ""
        self.signals = []
        self.dbcName = ""
        self.data = []
        self.txing = False

    def has_receiver(self, rec):
        for signal in self.signals:
            for receiver in signal.receivers:
                if rec == receiver:
                    return True

        return False

    def getHEXIDstrAndSignals(self):
        returnDict = {
            'id':self.id,
            'HEXIDstr':self.HEXIDstr,
            'signals':[item.getName() for item in self.signals],
        }
        return returnDict


class dbcMgr:
    def __init__(self):
        self.BIT_LEN_OF_1BYTE = 8
        self.DATA_SIZE_OF_A_CAN_MSG = 64
        self.bitPosOfDataBytes = [
            7,   6,   5,   4,   3,   2,   1,   0,
            15,  14,  13,  12,  11,  10,  9,   8,
            23,  22,  21,  20,  19,  18,  17,  16,
            31,  30,  29,  28,  27,  26,  25,  24,
            39,  38,  37,  36,  35,  34,  33,  32,
            47,  46,  45,  44,  43,  42,  41,  40,
            55,  54,  53,  52,  51,  50,  49,  48,
            63,  62,  61,  60,  59,  58,  57,  56,
            71,  70,  69,  68,  67,  66,  65,  64,
            79,  78,  77,  76,  75,  74,  73,  72,
            87,  86,  85,  84,  83,  82,  81,  80,
            95,  94,  93,  92,  91,  90,  89,  88,
            103, 102, 101, 100, 99,  98,  97,  96, 
            111, 110, 109, 108, 107, 106, 105, 104, 
            119, 118, 117, 116, 115, 114, 113, 112,
            127, 126, 125, 124, 123, 122, 121, 120,
            135, 134, 133, 132, 131, 130, 129, 128,
            143, 142, 141, 140, 139, 138, 137, 136,
            151, 150, 149, 148, 147, 146, 145, 144, 
            159, 158, 157, 156, 155, 154, 153, 152, 
            167, 166, 165, 164, 163, 162, 161, 160,
            175, 174, 173, 172, 171, 170, 169, 168, 
            183, 182, 181, 180, 179, 178, 177, 176, 
            191, 190, 189, 188, 187, 186, 185, 184, 
            199, 198, 197, 196, 195, 194, 193, 192, 
            207, 206, 205, 204, 203, 202, 201, 200, 
            215, 214, 213, 212, 211, 210, 209, 208, 
            223, 222, 221, 220, 219, 218, 217, 216, 
            231, 230, 229, 228, 227, 226, 225, 224, 
            239, 238, 237, 236, 235, 234, 233, 232, 
            247, 246, 245, 244, 243, 242, 241, 240, 
            255, 254, 253, 252, 251, 250, 249, 248, 
            263, 262, 261, 260, 259, 258, 257, 256, 
            271, 270, 269, 268, 267, 266, 265, 264, 
            279, 278, 277, 276, 275, 274, 273, 272, 
            287, 286, 285, 284, 283, 282, 281, 280, 
            295, 294, 293, 292, 291, 290, 289, 288, 
            303, 302, 301, 300, 299, 298, 297, 296, 
            311, 310, 309, 308, 307, 306, 305, 304, 
            319, 318, 317, 316, 315, 314, 313, 312, 
            327, 326, 325, 324, 323, 322, 321, 320, 
            335, 334, 333, 332, 331, 330, 329, 328, 
            343, 342, 341, 340, 339, 338, 337, 336, 
            351, 350, 349, 348, 347, 346, 345, 344, 
            359, 358, 357, 356, 355, 354, 353, 352, 
            367, 366, 365, 364, 363, 362, 361, 360, 
            375, 374, 373, 372, 371, 370, 369, 368, 
            383, 382, 381, 380, 379, 378, 377, 376, 
            391, 390, 389, 388, 387, 386, 385, 384, 
            399, 398, 397, 396, 395, 394, 393, 392, 
            407, 406, 405, 404, 403, 402, 401, 400, 
            415, 414, 413, 412, 411, 410, 409, 408, 
            423, 422, 421, 420, 419, 418, 417, 416, 
            431, 430, 429, 428, 427, 426, 425, 424, 
            439, 438, 437, 436, 435, 434, 433, 432, 
            447, 446, 445, 444, 443, 442, 441, 440, 
            455, 454, 453, 452, 451, 450, 449, 448, 
            463, 462, 461, 460, 459, 458, 457, 456, 
            471, 470, 469, 468, 467, 466, 465, 464, 
            479, 478, 477, 476, 475, 474, 473, 472, 
            487, 486, 485, 484, 483, 482, 481, 480, 
            495, 494, 493, 492, 491, 490, 489, 488, 
            503, 502, 501, 500, 499, 498, 497, 496, 
            511, 510, 509, 508, 507, 506, 505, 504
            ]

        self.bit_mask_for_OR  = [ 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80 ]
        self.bit_mask_for_AND = [ 0xFE, 0xFD, 0xFB, 0xF7, 0xEF, 0xDF, 0xBF, 0x7F ]
        self.parsedDBC = []

    def bitPacking(self, inputList, startBit, bitSize, value, byteOrder):
        bytePos = 0
        bitPos =  0xFFFF

        if bitSize == 0 or (bitSize > (self.BIT_LEN_OF_1BYTE * self.DATA_SIZE_OF_A_CAN_MSG)):
            return # Invalid Length

        if( byteOrder == 'Motorola' ):
            for i in range(0, (self.BIT_LEN_OF_1BYTE * self.DATA_SIZE_OF_A_CAN_MSG)):
                if(self.bitPosOfDataBytes[i] == startBit):
                    bitPos  = self.bitPosOfDataBytes[i + bitSize - 1]
                    bytePos = int(bitPos / self.BIT_LEN_OF_1BYTE)
                    bitPos = bitPos % self.BIT_LEN_OF_1BYTE
                    break
        else:
            bytePos = int(startBit / self.BIT_LEN_OF_1BYTE)
            bitPos = startBit % self.BIT_LEN_OF_1BYTE

        if bitPos == 0xFFFF:
            return # Fail to find bit position.

        for i in range(0, bitSize):
            if( (value >> i) & 0x01 ):
                inputList[bytePos] |= self.bit_mask_for_OR[bitPos]
            else:
                inputList[bytePos] &= self.bit_mask_for_AND[bitPos]

            bitPos += 1

            if( bitPos >= self.BIT_LEN_OF_1BYTE):
                if bytePos == 0 and byteOrder == 'Motorola':
                    break
                if byteOrder == 'Motorola':
                    bytePos -= 1
                else:
                    bytePos += 1
                    if bytePos >= self.DATA_SIZE_OF_A_CAN_MSG:
                        break
                
                bitPos = 0 # Reset to zero

    def bitUnpacking(self, inputList, startBit, bitSize, byteOrder):
        retVal  = 0
        bytePos = 0
        bitPos  = 0xFFFF
        bitPosOfretVal  = 0
        bytePosOfretVal = 0

        if bitSize == 0:
            return 0

        if byteOrder == 'Motorola':
            for i in range(0, (self.BIT_LEN_OF_1BYTE * self.BIT_LEN_OF_1BYTE)):
                if self.bitPosOfDataBytes[i] == startBit:
                    bitPos = self.bitPosOfDataBytes[i + bitSize - 1]
                    bytePos = int(bitPos / self.BIT_LEN_OF_1BYTE) # Calcurate byte position by using the bit position table.
                    bitPos  = bitPos % self.BIT_LEN_OF_1BYTE # set the bit position in one byte.
                    break
        else:
            bytePos = int(startBit / self.BIT_LEN_OF_1BYTE) # Calcurate byte position by using the bit position table.
            bitPos  = startBit % self.BIT_LEN_OF_1BYTE # set the bit position in one byte.

        if bitPos == 0xFFFF:
            return 0

        for i in range(0, bitSize):
            if inputList[bytePos] & self.bit_mask_for_OR[bitPos]:
                retVal |= ( self.bit_mask_for_OR[bitPosOfretVal] << (self.BIT_LEN_OF_1BYTE * bytePosOfretVal) ) # Bit Set
            else:
                retVal &= ~( self.bit_mask_for_OR[bitPosOfretVal] << (self.BIT_LEN_OF_1BYTE * bytePosOfretVal) ) # Bit Clear
            
            bitPos += 1
            if bitPos >= self.BIT_LEN_OF_1BYTE:
                if bytePos == 0 and byteOrder == 'Motorola':
                    break
                if byteOrder == 'Motorola':
                    bytePos -= 1
                else:
                    bytePos += 1
                bitPos = 0
            
            bitPosOfretVal += 1
            if bitPosOfretVal >= self.BIT_LEN_OF_1BYTE:
                bytePosOfretVal += 1
                bitPosOfretVal = 0
        return retVal

    def parseDBC(self, dbcFileName ):
        encodingTypes = ['ascii', 'utf-8', 'utf-16', 'iso-8859-15', 'cp437']
        messageList = []
        for encode in encodingTypes:
            try:
                f= open( dbcFileName, 'r', encoding=encode)
                messageList = self.readParseDBCFile(f, dbcFileName)
            except:
                print('Coding Type({}) Not Supported'.format(encode))
            else:
                print('Coding Type({}) Parsed'.format(encode))
                return messageList
        return None
    def readParsedDBC(self):
        signalsInfo = dict()
        for item in self.parsedDBC:
            result = item.getHEXIDstrAndSignals()
            for signalName in result['signals']:
                if signalName in signalsInfo:
                    signalsInfo[signalName].append(result['HEXIDstr'])
                    print('[W] signalName is Duplicated {} {}'.format(signalName,str(signalsInfo[signalName])))
                else:
                    signalsInfo[signalName] = [result['HEXIDstr']]
        return signalsInfo
    def readParseDBCFile(self, f, dbcFileName ):
        foundMessages = []
        # Token Parsing Test Routine
        for line in f.readlines():
            line = line.strip() # Remove left and right space
            line = re.sub(' +', ' ', line) # Replace the continuous spaces with one space character.

            tmpWordList = []
            tmpWordList = re.split(' ', line)
            if tmpWordList[0] == 'BO_':
                msg = Message()
                foundMessages.append(msg)
                msg.id      = tmpWordList[1]
                msg.HEXIDstr = str(hex(int(msg.id)))
                msg.name    = re.sub(':', '', tmpWordList[2]) # Remove ':' character in the message name. 
                msg.len     = int(tmpWordList[3])
                msg.emitter = tmpWordList[4]
                msg.dbcName = dbcFileName
                msg.data    = [0 for _ in range(msg.len)]
                msg.txing   = False
            elif tmpWordList[0] == 'SG_':
                sgnl = Signal()
                msg.signals.append(sgnl)

                tmpLine = re.sub('[|@,]', ' ', line)
                tmpLine = re.sub('[\(\)\[\]]', '', tmpLine)

                tmpWordList = []
                tmpWordList = re.split(' ', tmpLine)

                sgnl.name       = tmpWordList[1]
                sgnl.startBit   = int(tmpWordList[3])
                sgnl.bitSize    = int(tmpWordList[4])
                sgnl.byteOrder  = tmpWordList[5]
                sgnl.factor     = float(tmpWordList[6])
                sgnl.offset     = float(tmpWordList[7])
                sgnl.min        = float(tmpWordList[8])
                sgnl.max        = float(tmpWordList[9])
                sgnl.unit       = tmpWordList[10]
                for i in range(11, len(tmpWordList)):
                    if tmpWordList[i] != '':
                        sgnl.receivers.append(tmpWordList[i])

                if sgnl.byteOrder.find('0') == -1:
                    msg.byteOrderStr = 'Intel'
                else:
                    msg.byteOrderStr = 'Motorola'

        f.seek(0) # Set the file position to the top(start)
        for line in f.readlines():
            line = line.strip() # Remove left and right space
            line = re.sub(' +', ' ', line) # Replace the continuous spaces with one space character.

            tmpWordList = []
            tmpWordList = re.split(' ', line)
            if len(tmpWordList) > 2 and tmpWordList[0] == 'BA_' and tmpWordList[1] == '"GenMsgCycleTime"':
                for item in foundMessages:
                    if item.id == tmpWordList[3]:
                        tmpWordList[4] = re.sub(';', '', tmpWordList[4]) # remove ';' character. 
                        if tmpWordList[4] == '':
                            item.period = 0
                        else:
                            item.period = int(tmpWordList[4])
                        break
            elif len(tmpWordList) >= 3 and tmpWordList[0] == 'VAL_':
                for item in foundMessages:
                    if item.id == tmpWordList[1]:
                        for sig in item.signals:
                            if sig.name == tmpWordList[2]: # Find signal matched with name
                                tmpStr = ''
                                for i in range(3, len(tmpWordList)):
                                    if tmpWordList[i] == ';' or '':
                                        break

                                    tmpStr += tmpWordList[i]

                                tmpValDescList = []
                                tmpValDescList = re.split('"', tmpStr)
                                tmpStr = ''
                                for i in range(0, len(tmpValDescList)):
                                    if tmpValDescList[i] == '':
                                        break
                                    if (i % 2) == 0:
                                        tmpStr += tmpValDescList[i] + ':'
                                    else:
                                        tmpStr += '"' + tmpValDescList[i] +'",'

                                # tmpStr = tmpStr.rstrip(',') # Remove ',' character from right side.
                                if tmpStr != '':
                                    n = tmpStr.rfind('"')
                                    tmpStr = tmpStr[0:n+1]

                                tmpStr = '{' + tmpStr + '}'

                                try:
                                    sig.valueDesc = ast.literal_eval(tmpStr)
                                except:
                                    sig.valueDesc = '' # Just set with null if there is no valid value description in this DBC file. 
                                    print('Fail to parse value description')

            elif len(tmpWordList) >= 3 and tmpWordList[0] == 'CM_' and tmpWordList[1] == "SG_":
                for item in foundMessages:
                    if item.id == tmpWordList[2]:
                        for sig in item.signals:
                            if sig.name == tmpWordList[3]: # Find signal matched with name
                                tmpStrList = []
                                tmpStrList = re.split('"', line)
                                sig.comment = tmpStrList[1]

        for msg in foundMessages:
            msg.id = int(msg.id) # Convert string to int

        if len(foundMessages) > 0 :
            self.parsedDBC = sorted(foundMessages, key=operator.attrgetter('name')) # Sort a list by name attribute.
            return True
        else:
            return False

    def updateSig(self, msgID, sigName, value): # Update a signal value and return message ID, message Len, Cycle Time, and message data
        if len(self.parsedDBC) > 0:
            for msg in self.parsedDBC:
                if msg.id == msgID:
                    # update the message data with signal values. 
                    for sig in msg.signals:
                        if sig.name == sigName:
                            sig.value = value
                            self.bitPacking( msg.data, sig.startBit, sig.bitSize, sig.value, msg.byteOrderStr)
                            return msg.id, msg.len, msg.period, msg.data
        return 0, 0, 0, []

    def clearMsg(self): # Clear all message data. 
        for msg in self.parsedDBC:
            msg.data = [0 for _ in range(msg.len)]
            for sig in msg.signals:
                sig.value = 0

