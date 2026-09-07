"""
Kartin hangi urun paketine cevap verdigini bulan tarama.

Kutuphanedeki her cihaz sinifinin gonderdigi cerceve, sirayla ve tamamen sifir
payload ile (enable=0, motor=0) gonderilir; karttan donen HAM byte'lar basilir.
Hicbir cerceve harekete sebep olmaz.

Amac: get_board_info (0xFC) cevap verirken Stewart (0xBE) neden sessiz kaliyor,
kart baska bir DEVID'e mi cevap veriyor sorusunu netlestirmek.
"""
import struct
import time

import serial
from crccheck.crc import Crc32Mpeg2 as CRC32

PORT = "/dev/ttyAMA0"
BAUD = 115200
HEADER = 0x55
SETTLE = 0.15  # cevabin tamaminin gelmesi icin beklenen sure

# (isim, gonderilecek struct formati, argumanlar, beklenen cevap boyu)
PROBES = [
    ("Ping           0x00", "<BB", (HEADER, 0x00), 6),
    ("BoardInfo      0xFC", "<BBBI", (HEADER, 0xFC, 0, 0), 19),
    ("OneDOF         0xBA", "<BBBh", (HEADER, 0xBA, 0, 0), 22),
    ("BallBeam       0xBB", "<BBh", (HEADER, 0xBB, 0), 8),
    ("BallBalancing  0xBC", "<BBhh", (HEADER, 0xBC, 0, 0), 10),
    ("Delta          0xBD", "<BBBhhh", (HEADER, 0xBD, 0, 0, 0, 0), 12),
    ("Stewart        0xBE", "<BBBhhhhhh", (HEADER, 0xBE, 0, 0, 0, 0, 0, 0, 0), 30),
    ("Pendulum       0xBF", "<BBBh", (HEADER, 0xBF, 0, 0), 10),
    ("StewartEnc     0xC0", "<BBBhhhhhh", (HEADER, 0xC0, 0, 0, 0, 0, 0, 0, 0), 30),
    ("StewartEncHR   0xC1", "<BBBhhhhhh", (HEADER, 0xC1, 0, 0, 0, 0, 0, 0, 0), 42),
]

ph = serial.Serial(port=PORT, baudrate=BAUD, timeout=0.3)

print(f"{'CIHAZ':22} {'GONDERILEN':>10} {'GELEN':>7}  DURUM")
print("-" * 78)

for name, fmt, args, expected in PROBES:
    payload = struct.pack(fmt, *args)
    frame = payload + CRC32.calc(payload).to_bytes(4, "little")

    ph.reset_input_buffer()
    ph.write(frame)
    ph.flush()
    time.sleep(SETTLE)

    resp = ph.read(ph.in_waiting) if ph.in_waiting else b""

    if not resp:
        status = "cevap yok"
    else:
        bits = []
        bits.append(f"header 0x{resp[0]:02x}")
        if len(resp) > 1:
            bits.append(f"devid 0x{resp[1]:02x}")
        if len(resp) >= 5:
            crc_ok = CRC32.calc(resp[:-4]).to_bytes(4, "little") == resp[-4:]
            bits.append(f"CRC {'OK' if crc_ok else 'HATALI'}")
        if len(resp) != expected:
            bits.append(f"BEKLENEN {expected}")
        status = " | ".join(bits)

    print(f"{name:22} {len(frame):>10} {len(resp):>7}  {status}")
    if resp:
        print(f"{'':22} {'':>10} {'':>7}  hex={resp.hex()}")

ph.close()
