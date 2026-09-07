import serial
import struct
from crccheck.crc import Crc32Mpeg2 as CRC32

PORT = "/dev/serial0"
BAUD = 115200

ph = serial.Serial(port=PORT, baudrate=BAUD, timeout=1.0)

HEADER = 0x55
CFG_DEVID = 0xFC
CMD_NULL = 0

data = struct.pack("<BBBI", HEADER, CFG_DEVID, CMD_NULL, 0)
data += CRC32.calc(data).to_bytes(4, 'little')

print("Gonderilen bytes:", data.hex())
ph.reset_input_buffer()
ph.write(data)

raw = ph.read(19)
print("Alinan byte sayisi:", len(raw))
print("Alinan bytes (hex):", raw.hex())

if len(raw) > 0:
    print("Ilk byte (header beklenen 0x55):", hex(raw[0]))
