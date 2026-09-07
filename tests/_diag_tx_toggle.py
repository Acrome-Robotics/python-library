import serial
import time

PORT = "/dev/serial0"
BAUD = 9600  # dusuk baud, multimetreyle gorsel takip icin

ph = serial.Serial(port=PORT, baudrate=BAUD, timeout=0.1)

print("Surekli 0x55 gonderiliyor... Ctrl+C ile durdurun.")
print("Multimetre DC voltaj modunda TXD (pin 8) - GND (pin 6) arasini olcun.")
print("Idle: ~3.3V. Veri gonderilirken ortalama deger biraz dusecek/dalgalanacak.")

try:
    while True:
        ph.write(bytes([0x55]) * 50)
        time.sleep(0.05)
except KeyboardInterrupt:
    pass
