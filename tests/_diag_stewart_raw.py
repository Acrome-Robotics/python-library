"""
Stewart paketine karttan gelen HAM cevabi dokan teshis scripti.

stewart_keyboard_control.py'de err sayaci artiyorsa sebebi burada gorulur:
  - hic byte gelmiyorsa  -> kart 0xBE (Stewart) paketine cevap vermiyor
  - 30'dan farkli sayida byte geliyorsa -> paket boyu/mod uyusmuyor
  - header 0x55 degilse  -> tampon hizalamasi kaymis
  - CRC tutmuyorsa       -> baud/hat kalitesi ya da firmware farki
"""
import struct
import time

import serial
from crccheck.crc import Crc32Mpeg2 as CRC32

PORT = "/dev/ttyAMA0"
BAUD = 115200

HEADER = 0x55
CFG_DEVID = 0xFC
STEWART_DEVID = 0xBE
CMD_NULL = 0


def framed(payload):
    return payload + CRC32.calc(payload).to_bytes(4, "little")


ph = serial.Serial(port=PORT, baudrate=BAUD, timeout=0.3)

# 1) Board info: kartin genel olarak konustugunu dogrular
ph.reset_input_buffer()
ph.write(framed(struct.pack("<BBBI", HEADER, CFG_DEVID, CMD_NULL, 0)))
info = ph.read(19)
print(f"board_info  : {len(info)} byte -> {info.hex()}")
if len(info) == 19 and info[0] == HEADER:
    sw = list(info)[2:5][::-1]
    hw = list(info)[6:9][::-1]
    print(f"              SW {sw[0]}.{sw[1]}.{sw[2]}  HW {hw[0]}.{hw[1]}.{hw[2]}")
print(f"artan byte  : {ph.in_waiting}")
print()

# 2) Stewart paketi: motorlar 0, enable 0 -> hareket olmaz
# Firmware'de receiveCount 7 -> 8 oldu (EN, MT[1..6], Digital_Pins), yani
# motorlardan sonra 1 bytelik Digital_Pins alani eklendi. Cerceve 19 -> 20 byte.
packet = framed(struct.pack("<BBBhhhhhhB", HEADER, STEWART_DEVID, 0, 0, 0, 0, 0, 0, 0, 0))
print(f"gonderilen  : {packet.hex()}  ({len(packet)} byte)")
print()

for i in range(10):
    ph.reset_input_buffer()
    ph.write(packet)
    time.sleep(0.1)  # cevabin tamaminin gelmesini bekle

    n = ph.in_waiting
    resp = ph.read(n) if n else b""

    line = f"[{i}] gelen {len(resp):3d} byte"
    if resp:
        line += f" | header 0x{resp[0]:02x} | devid 0x{resp[1]:02x}" if len(resp) > 1 else ""
        if len(resp) == 30:
            crc_ok = CRC32.calc(resp[:-4]).to_bytes(4, "little") == resp[-4:]
            line += f" | CRC {'OK' if crc_ok else 'HATALI'}"
            if crc_ok:
                pos = struct.unpack("<HHHHHH", resp[2:14])
                imu = struct.unpack("<fff", resp[14:26])
                line += f"\n    pos={pos} imu={tuple(round(v, 2) for v in imu)}"
        line += f"\n    hex={resp.hex()}"
    print(line)

ph.close()
