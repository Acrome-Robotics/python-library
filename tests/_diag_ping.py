from acrome import controller

dev = controller.Stewart("/dev/serial0", baudrate=115200)


while True:
    print(dev.ping())