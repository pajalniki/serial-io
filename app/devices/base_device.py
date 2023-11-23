import serial
from app.services import consoleService, Console
from .devices_enums import DeviceType

class BaseDevice():
    __serial: serial.Serial
    console: Console
    code: str = None
    type: DeviceType = None


    def __init__(self, serial: serial.Serial) -> None:
        self.__serial = serial
        self.console = consoleService.console(self)
        pass


    def read_code(self):
        got_str = self.__serial.readline().decode('ascii')
        splitting = got_str.replace('/n', '').strip().split()
        
        # По умолчанию
        device_type = DeviceType.INPUT_DEVICE

        if (len(splitting) == 2):
            (device_type, code) = code
        elif (len(splitting) == 1):
            code = splitting[0]

        if (code):
            self.type = device_type
            self.code = code
            self.console.log(f'Устройство {self.__serial.port} опознано как {self.code}, тип: {self.type}')
            self.__serial.write('OK')
            
            self = switch_device(self)
        else:
            self.console.log(f'Устройство {self.__serial.port} не отправило код')


    async def run_single(self):
        if not self.code:
            self.read_code()


def switch_device(base_device: BaseDevice) -> BaseDevice:
    if base_device.type == DeviceType.INPUT_DEVICE:
        from .input_device import InputDevice
        return InputDevice(base_device.__serial, base_device.code, base_device.type)
    return base_device