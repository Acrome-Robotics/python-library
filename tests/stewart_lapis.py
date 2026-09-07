from acrome import controller

dev = controller.Stewart("COM8", baudrate=115200)


while True:
    dev.enable(True)
    dev.set_motors([0, 0, 0, 0, 0, 0]) 
    dev.update()