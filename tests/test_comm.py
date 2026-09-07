from acrome.controller import *

dev = Pendulum("COM8", 115200)

dev.enable(True)
while(True):
    print(dev.encoder)
    print(dev.position)
    dev.set_motor(333)
    print(dev.update())