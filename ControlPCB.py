import sys

import serial.tools.list_ports
from serial import SerialException

def ControlPCB(signal):
    ser = serial.Serial('/dev/arduino', 9600)
    num = bytes(str(signal), 'ascii')
    try:
        # print("Start enable USB DEBUG")
        ser.write(num)
    except SerialException as e:
        print("Please plugin Virtual Keyboard")
        print(e)
if __name__ == '__main__':
    ControlPCB(str(sys.argv[1]))
