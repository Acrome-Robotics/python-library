import time

from acrome import controller

port = "/dev/serial0"

dev = controller.Pendulum(port, 115200)

dev.enable(True)


pwm = -900
while True:
    print(dev.ping())
    time.sleep(0.01)


while True:
    print("Encoder:", dev.encoder)
    print("Position:", dev.position)
    dev.set_motor(300)
    print("Update:", dev.update())