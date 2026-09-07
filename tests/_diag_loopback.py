import serial
import time

PORT = "/dev/serial0"
BAUD = 115200

# GPIO14 (TXD, pin 8) ile GPIO15 (RXD, pin 10) arasina jumper kablo takin.

ph = serial.Serial(port=PORT, baudrate=BAUD, timeout=0.5)
ph.reset_input_buffer()

test_data = b"ACROME_LOOPBACK_TEST"

print("Gonderiliyor:", test_data)
ph.write(test_data)
time.sleep(0.1)

received = ph.read(len(test_data))
print("Alinan       :", received)

if received == test_data:
    print("BASARILI: Loopback calisti, TX ve RX donanimsal olarak dogru.")
elif len(received) == 0:
    print("HATA: Hic veri gelmedi. TX fiziksel olarak veri gondermiyor olabilir")
    print("      ya da jumper kablo dogru takilmamis olabilir.")
else:
    print("HATA: Kismi/bozuk veri geldi. Baud rate veya kablo baglantisini kontrol edin.")
