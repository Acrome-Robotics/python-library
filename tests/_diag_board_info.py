import serial
from acrome.controller import Controller

PORT = "/dev/serial0"
BAUD = 115200

c = Controller.__new__(Controller)
c._Controller__ph = serial.Serial(port=PORT, baudrate=BAUD, timeout=0.5)
info = c.get_board_info()
print("board_info:", info)
