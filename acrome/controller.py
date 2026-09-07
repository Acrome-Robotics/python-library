import serial
from crccheck.crc import Crc32Mpeg2 as CRC32
import struct
from stm32loader.main import main as stm32loader_main
import tempfile
import requests
import hashlib
from packaging.version import parse as parse_version

class UnsupportedFirmware(Exception):
    pass
class UnsupportedHardware(Exception):
    pass

class Controller():
    _HEADER = 0x55
    _ID_INDEX = 1
    _CFG_DEVID = 0xFC
    _PING_DEVID = 0x00
    _CMD_NULL = 0
    _CMD_REBOOT = (1 << 0)
    _CMD_BL = (1 << 1)
    _STATUS_KEY_LIST = ['EEPROM', 'IMU', 'Touchscreen Serial', 'Touchscreen Analog', 'Delta', 'Software Version', 'Hardware Version']

    def __init__(self, portname="/dev/serial0", baudrate=115200):
        self.__ph = serial.Serial(port=portname, baudrate=baudrate, timeout=0.1)
        self.__serial_settings = self.__ph.get_settings()
        self.__fw_file = None
        self.board_info = self.get_board_info()
        self.__release_url = None

        if self.board_info is not None:
            if parse_version(self.board_info["Hardware Version"]) < parse_version('2.0.0'):
                self.__release_url = "https://api.github.com/repos/acrome-robotics/Acrome-Controller-Firmware/releases/{version}"
            else:
                self.__release_url = "https://api.github.com/repos/acrome-robotics/Acrome-Controller-Firmware-v2/releases/{version}"

    def __del__(self):
        try:
            if self.__ph.isOpen():
                self.__ph.flush()
                self.__ph.flushInput()
                self.__ph.flushOutput()
                self.__ph.close()
        except AttributeError:
            pass
        except Exception as e:
            raise e

    def _writebus(self, data):
        self.__ph.write(data)

    def _readbus(self, byte_count):
        data = self.__ph.read(byte_count)
        if len(data) == byte_count:
            if data[0] == self.__class__._HEADER:
                if self._crc32(data[:-4]) == data[-4:]:
                    return data
        return None

    def reboot(self):
        data = 0
        data = struct.pack("<BBBI", self.__class__._HEADER, self.__class__._CFG_DEVID, self.__class__._CMD_REBOOT, data)
        data += self._crc32(data)
        self._writebus(data)

    def enter_bootloader(self):
        data = 0
        data = data = struct.pack("<BBBI", self.__class__._HEADER, self.__class__._CFG_DEVID, self.__class__._CMD_BL, data)
        data += self._crc32(data)
        self._writebus(data)

    def get_latest_version(self):
        response = requests.get(url=self.__release_url.format(version='latest'))
        if (response.status_code in [200, 302]):
            return(response.json()['tag_name'])

    def fetch_fw_binary(self, version=''):

        self.__fw_file = tempfile.NamedTemporaryFile("wb+")
 
        if version == '':
            
            version='latest'
        else:
            version = 'tags/' + version

        #Get asset list from GitHub repository
        response = requests.get(url=self.__release_url.format(version=version))
        if (response.status_code in [200, 302]):
            assets = response.json()['assets']

            fw_dl_url = None
            md5_dl_url = None
            for asset in assets:
                if '.bin' in asset['name']:
                    fw_dl_url = asset['browser_download_url']
                elif '.md5' in asset['name']:
                    md5_dl_url = asset['browser_download_url']

            if None in [fw_dl_url, md5_dl_url]:
                raise Exception("Could not found requested firmware file! Check your connection to GitHub.")

            #Get binary firmware file
            md5_fw = None
            response = requests.get(fw_dl_url, stream=True)
            if (response.status_code in [200, 302]):
                self.__fw_file.write(response.content)
                md5_fw = hashlib.md5(response.content).hexdigest()
            else:
                raise Exception("Could not fetch requested binary file! Check your connection to GitHub.")

            #Get MD5 file
            response = requests.get(md5_dl_url, stream=True)
            if (response.status_code in [200, 302]):
                md5_retreived = response.text.split(' ')[0]
                if (md5_fw == md5_retreived):
                    return True
                else:
                    raise Exception("MD5 Mismatch!")
            else:
                raise Exception("Could not fetch requested MD5 file! Check your connection to GitHub.")

        else:
            raise Exception("Could not found requested firmware files list! Check your connection to GitHub.")

    def update_fw_binary(self, baudrate = 115200):
        if (baudrate > 115200):
            baudrate = 115200
        elif (baudrate < 1200):
            baudrate = 1200

        try:
            self.__fw_file.read()    
        except AttributeError:
            raise Exception("Firmware file must be fetched first!")
        except Exception as e:
            raise e

        self.__ph.close() #Close serial port to give full control to the stm32loader
        args = ['-p', self.__ph.portstr, '-b', str(baudrate), '-e', '-w', '-v', self.__fw_file.name]
        stm32loader_main(*args)
        if (not self.__fw_file.closed):
            self.__fw_file.close() #This will permanently delete the file

        self.__ph.apply_settings(self.__serial_settings)
        self.__ph.open() #Re-open serial port

    def ping(self):
        data = struct.pack("<BB", self.__class__._HEADER, self.__class__._PING_DEVID)
        data += self._crc32(data)
        self._writebus(data)
        r = self._readbus(6)
        if r is not None:
            if r[self.__class__._ID_INDEX] == self.__class__._PING_DEVID:
                return True
        return False

    def get_board_info(self):
        data = 0
        data = struct.pack("<BBBI", self.__class__._HEADER, self.__class__._CFG_DEVID, self.__class__._CMD_NULL, data)
        data += self._crc32(data)
        self._writebus(data)
        r = self._readbus(19)
        st = dict([])
        if r is not None:
            for pos, key in enumerate(self.__class__._STATUS_KEY_LIST):
                st[key] = bool((r[10] & (1 << pos)) >> pos)
            ver = list(r)[2:5]
            st['Software Version'] = "{0}.{1}.{2}".format(*ver[::-1])
            ver = list(r)[6:9]
            st['Hardware Version'] = "{0}.{1}.{2}".format(*ver[::-1])
            return st
        return None

    def _crc32(self, data):
        return CRC32.calc(data).to_bytes(4, 'little')

    def update(self):
        if self.__class__ is not Controller:
            self._write()
            return self._read()
        else:
            raise NotImplementedError


class OneDOF(Controller):
    _DEVID = 0xBA
    _EN_MASK = 1 << 0
    _ENC1_RST_MASK = 1 << 1
    _ENC2_RST_MASK = 1 << 2
    _RECEIVE_COUNT = 22
    _MAX_SPEED_ABS = 1000

    def __init__(self, portname="/dev/serial0", baudrate=115200):
        super().__init__(portname=portname, baudrate=baudrate)
        self.__config = 0
        self.__speed = 0
        self.angle = 0
        self.motor_enc = 0
        self.shaft_enc = 0
        self.imu = [0,0,0]

    def __del__(self):
        super().__del__()

    def set_speed(self, speed):
        if speed != 0:
            self.__speed = int(speed if abs(speed) <= self.__class__._MAX_SPEED_ABS else self.__class__._MAX_SPEED_ABS * (speed / abs(speed)))
        else:
            self.__speed = int(speed)

    def enable(self, en):
        self.__config = (self.__config & ~self.__class__._EN_MASK) | (en & self.__class__._EN_MASK)

    def reset_encoder_mt(self):
        self.__config |= self.__class__._ENC1_RST_MASK

    def reset_encoder_shaft(self):
        self.__config |= self.__class__._ENC2_RST_MASK

    def _write(self):
        data = struct.pack("<BBBh", self.__class__._HEADER, self.__class__._DEVID, self.__config, self.__speed)
        data += self._crc32(data)
        super()._writebus(data)
        self.__config &= self.__class__._EN_MASK

    def _read(self):
        data = super()._readbus(self.__class__._RECEIVE_COUNT)
        if data is not None:
            if data[self.__class__._ID_INDEX] == self.__class__._DEVID:
                self.motor_enc = struct.unpack("<H", data[2:4])[0]
                self.shaft_enc = struct.unpack("<H", data[4:6])[0]
                self.imu = list(struct.unpack("<fff", data[6:18]))
                return True
        return False


class BallBeam(Controller):
    _DEVID = 0xBB
    _MAX_SERVO_ABS = 1000
    _RECEIVE_COUNT = 8

    def __init__(self, portname="/dev/serial0", baudrate=115200):
        super().__init__(portname=portname, baudrate=baudrate)
        self.position = 0
        self.__servo = 0

    def __del__(self):
        super().__del__()

    def set_servo(self, servo):
        if servo != 0:
            self.__servo = int(servo if abs(servo) <= self.__class__._MAX_SERVO_ABS else self.__class__._MAX_SERVO_ABS * (servo / abs(servo)))
        else:
            self.__servo = int(servo)

    def _write(self):
        data = struct.pack("<BBh", self.__class__._HEADER, self.__class__._DEVID, self.__servo)
        data += self._crc32(data)
        super()._writebus(data)

    def _read(self):
        data = super()._readbus(self.__class__._RECEIVE_COUNT)
        if data is not None:
            if data[self.__class__._ID_INDEX] == self.__class__._DEVID:
                self.position = struct.unpack("<h", data[2:4])[0]
                return True
        return False


class BallBalancingTable(Controller):
    _DEVID = 0xBC
    _MAX_SERVO_ABS = 1000
    _RECEIVE_COUNT = 10

    def __init__(self, portname="/dev/serial0", baudrate=115200):
        super().__init__(portname=portname, baudrate=baudrate)
        self.__servo = [0,0]
        self.position = [0,0]

    def __del__(self):
        super().__del__()

    def set_servo(self, x, y):
        if x != 0:
            self.__servo[0] = int(x if abs(x) <= self.__class__._MAX_SERVO_ABS else self.__class__._MAX_SERVO_ABS * (x / abs(x)))
        else:
            self.__servo[0] = int(x)

        if y != 0:
            self.__servo[1] = int(y if abs(x) <= self.__class__._MAX_SERVO_ABS else self.__class__._MAX_SERVO_ABS * (y / abs(y)))
        else:
            self.__servo[1] = int(y)

    def _write(self):
        data = struct.pack("<BBhh", self.__class__._HEADER, self.__class__._DEVID, self.__servo[0], self.__servo[1])
        data += self._crc32(data)
        super()._writebus(data)

    def _read(self):
        data = super()._readbus(self.__class__._RECEIVE_COUNT)
        if data is not None:
            if data[self.__class__._ID_INDEX] == self.__class__._DEVID:
                self.position = list(struct.unpack("<hh", data[2:6]))
                return True
        return False


class Delta(Controller):
    _DEVID = 0xBD
    _MAX_MT_POS = 810
    _MIN_MT_POS = 310
    _RECEIVE_COUNT = 12

    def __init__(self, portname="/dev/serial0", baudrate=115200):
        super().__init__(portname=portname, baudrate=baudrate)
        self.__magnet = 0
        self.__motors = [0] * 3
        self.position = [0] * 3

    def __del__(self):
        super().__del__()

    def pick(self, magnet):
        self.__magnet = magnet & 0x01

    def set_motors(self, motors):
        if len(motors) != 3:
            raise Exception("Argument motors must have length of 3")

        for i, motor in enumerate(motors):
            if motor <= self.__class__._MAX_MT_POS and motor >= self.__class__._MIN_MT_POS:
                self.__motors[i] = int(motor)
            else:
                if motor >= self.__class__._MAX_MT_POS:
                    self.__motors[i] = int(self.__class__._MAX_MT_POS)
                else:
                    self.__motors[i] = int(self.__class__._MIN_MT_POS)

    def _write(self):
        data = struct.pack("<BBBhhh", self.__class__._HEADER, self.__class__._DEVID, self.__magnet, *self.__motors)
        data += self._crc32(data)
        super()._writebus(data)

    def _read(self):
        data = super()._readbus(self.__class__._RECEIVE_COUNT)
        if data is not None:
            if data[self.__class__._ID_INDEX] == self.__class__._DEVID:
                self.position = list(struct.unpack("<HHH", data[2:8]))
                return True
        return False


class Pendulum(Controller):
    _DEVID = 0xBF
    _MAX_MT_SPEED = 1000
    _MIN_MT_SPEED = -1000
    _EN_MASK = 1 << 0
    _ENC1_RST_MASK = 1 << 1
    _RECEIVE_COUNT = 10

    def __init__(self, portname="/dev/serial0", baudrate=115200):
        super().__init__(portname=portname, baudrate=baudrate)
        self.__motor = 0
        self.__config = 0
        self.position = 0
        self.encoder = 0

    def __del__(self):
        super().__del__()

    def set_motor(self, motor):
        if motor <= self.__class__._MAX_MT_SPEED and motor >= self.__class__._MIN_MT_SPEED:
            self.__motor = int(motor)
        else:
            if motor >= self.__class__._MAX_MT_SPEED:
                self.__motor = int(self.__class__._MAX_MT_SPEED)
            else:
                self.__motor = int(self.__class__._MIN_MT_SPEED)

    def enable(self, en):
        self.__config = (self.__config & ~self.__class__._EN_MASK) | (en & self.__class__._EN_MASK)

    def reset_encoder_mt(self):
        self.__config |= self.__class__._ENC1_RST_MASK

    def _write(self):
        data = struct.pack("<BBBh", self.__class__._HEADER, self.__class__._DEVID, self.__config, self.__motor)
        data += self._crc32(data)
        super()._writebus(data)

    def _read(self):
        data = super()._readbus(self.__class__._RECEIVE_COUNT)
        if data is not None:
            if data[self.__class__._ID_INDEX] == self.__class__._DEVID:
                self.position = list(struct.unpack("<H", data[2:4]))[0]
                self.encoder = list(struct.unpack("<H", data[4:6]))[0]
                return True
        return False


class Stewart(Controller):
    _DEVID = 0xBE
    _MAX_MT_ABS = 1000
    _RECEIVE_COUNT = 30

    def __init__(self, portname="/dev/serial0", baudrate=115200):
        super().__init__(portname=portname, baudrate=baudrate)
        self.__en = 0
        self.__motors = [0] * 6
        self.__digital_pins = 0
        self.position = [0] * 6
        self.imu = [0] * 9

        if parse_version(self.board_info['Hardware Version']) <= parse_version('1.1.0'):
            raise UnsupportedHardware("Stewart is only available on Acrome Controller hardware version 1.2.0 or later. Your version is {}".format(self.board_info['Hardware Version']))

    def __del__(self):
        super().__del__()

    def enable(self, en):
        self.__en = (self.__en & ~0x01) | (en & 0x01)

    def set_motors(self, motors):
        if len(motors) != 6:
            raise Exception("Argument motors must have length of 6")

        for i, motor in enumerate(motors):
            if motor != 0:
                self.__motors[i] = int(motor if abs(motor) <= self.__class__._MAX_MT_ABS else self.__class__._MAX_MT_ABS * (motor / abs(motor)))
            else:
                self.__motors[i] = int(motor)

    def set_digital_pins(self, pins):
        self.__digital_pins = int(pins) & 0xFF

    def _write(self):
        data = struct.pack("<BBBhhhhhhB", self.__class__._HEADER, self.__class__._DEVID, self.__en, *self.__motors, self.__digital_pins)
        data += self._crc32(data)
        super()._writebus(data)
        self.__en &= 0x01

    def _read(self):
        data = super()._readbus(self.__class__._RECEIVE_COUNT)
        if data is not None:
            if data[self.__class__._ID_INDEX] == self.__class__._DEVID:
                self.position = list(struct.unpack("<HHHHHH", data[2:14]))
                self.imu = list(struct.unpack("<fff", data[14:26]))
                return True
        return False


class StewartEncoder(Controller):
    _DEVID = 0xC0
    _MAX_MT_ABS = 1000
    _RECEIVE_COUNT = 30

    def __init__(self, portname="/dev/serial0", baudrate=115200):
        super().__init__(portname=portname, baudrate=baudrate)
        self.__en = 0
        self.__motors = [0] * 6
        self.position = [0] * 6
        self.imu = [0] * 3

        if parse_version(self.board_info['Hardware Version']) <= parse_version('1.1.0'):
            raise UnsupportedHardware("Stewart is only available on Acrome Controller hardware version 1.2.0 or later. Your version is {}".format(self.board_info['Hardware Version']))

        if parse_version(self.board_info['Software Version']) < parse_version('1.5.0'):
            raise UnsupportedFirmware("Stewart is only available on Acrome Controller software version 1.5.0 or later. Your version is {}".format(self.board_info['Software Version']))

    def __del__(self):
        super().__del__()

    def enable(self, en):
        self.__en = (self.__en & ~0x01) | (en & 0x01)
    
    def reset_encoder(self, motor_num=[1,2,3,4,5,6]):
        for mt in motor_num:
            if (mt <= 6 and mt >= 1):
                self.__en |= 1 << (mt - 1 + 2)
            else:
                raise ValueError("Motor index can not be lower than 1 or higher than 6!")

    def set_motors(self, motors):
        if len(motors) != 6:
            raise Exception("Argument motors must have length of 6")

        for i, motor in enumerate(motors):
            if motor != 0:
                self.__motors[i] = int(motor if abs(motor) <= self.__class__._MAX_MT_ABS else self.__class__._MAX_MT_ABS * (motor / abs(motor)))
            else:
                self.__motors[i] = int(motor)

    def _write(self):
        data = struct.pack("<BBBhhhhhh", self.__class__._HEADER, self.__class__._DEVID, self.__en, *self.__motors)
        data += self._crc32(data)
        super()._writebus(data)
        self.__en &= 0x01

    def _read(self):
        data = super()._readbus(self.__class__._RECEIVE_COUNT)
        if data is not None:
            if data[self.__class__._ID_INDEX] == self.__class__._DEVID:
                self.position = list(struct.unpack("<HHHHHH", data[2:14]))
                self.imu = list(struct.unpack("<fff", data[14:26]))
                return True
        return False


class StewartEncoderHR(StewartEncoder):
    _DEVID = 0xC1
    _MAX_MT_ABS = 1000
    _RECEIVE_COUNT = 42

    def __init__(self, portname="/dev/serial0", baudrate=115200):
        super().__init__(portname=portname, baudrate=baudrate)
        self.__en = 0
        self.__motors = [0] * 6
        self.position = [0] * 6
        self.imu = [0] * 3

    def enable(self, en):
        self.__en = (self.__en & ~0x01) | (en & 0x01)

    def reset_encoder(self, motor_num=[1,2,3,4,5,6]):
        for mt in motor_num:
            if (mt <= 6 and mt >= 1):
                self.__en |= 1 << (mt - 1 + 2)
            else:
                raise ValueError("Motor index can not be lower than 1 or higher than 6!")

    def set_motors(self, motors):
        if len(motors) != 6:
            raise Exception("Argument motors must have length of 6")

        for i, motor in enumerate(motors):
            if motor != 0:
                self.__motors[i] = int(motor if abs(motor) <= self.__class__._MAX_MT_ABS else self.__class__._MAX_MT_ABS * (motor / abs(motor)))
            else:
                self.__motors[i] = int(motor)


    def _write(self):
        data = struct.pack("<BBBhhhhhh", self.__class__._HEADER, self.__class__._DEVID, self.__en, *self.__motors)
        data += self._crc32(data)
        super()._writebus(data)
        self.__en &= 0x01

    def _read(self):
        data = super()._readbus(self.__class__._RECEIVE_COUNT)
        if data is not None:
            if data[self.__class__._ID_INDEX] == self.__class__._DEVID:
                self.position = list(struct.unpack("<IIIIII", data[2:26]))
                self.imu = list(struct.unpack("<fff", data[26:38]))
                return True
        return False