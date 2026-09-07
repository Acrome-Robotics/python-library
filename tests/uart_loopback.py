import sys, time, serial
port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyAMA0"
baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200
s = serial.Serial(port, baud, timeout=1)
s.reset_input_buffer()
msg = b"PI5-UART-TEST\n"
s.write(msg); s.flush()
time.sleep(0.2)
back = s.read(len(msg))
print("gonderilen:", msg)
print("okunan    :", back)
print("SONUC     :", "OK - loopback calisiyor" if back == msg else "FAIL - veri donmedi")
s.close()
