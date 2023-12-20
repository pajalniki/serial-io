import serial
from app.model import AbstractSingleRunner
from app.services import consoleService, Console
from .devices_enums import DeviceType

class Device(AbstractSingleRunner):
    _serial: serial.Serial
    console: Console
    code: str = None
    type: DeviceType = None

    _runner: AbstractSingleRunner
    
    @property
    def active(self):
        return self._serial.is_open


    def kill(self):
        self._serial.close()
        return


    def __init__(self, serial: serial.Serial) -> None:
        self._serial = serial
        self.console = consoleService.console(self)
        pass


    def read_code(self):
        got_str = self._serial.readline().decode('ascii')
        code = got_str.replace('/n', '').strip()
        
        # По умолчанию
        device_type = DeviceType.INPUT_DEVICE

        if (code):
            self.type = device_type
            self.code = code
            self.console.log(f'Устройство {self._serial.port} опознано как {self.code}, тип: {self.type}')
            
            self._runner = device_factory(self)
            self._serial.write(str.encode('OK'))
        else:
            self.console.log(f'Устройство {self._serial.port} не отправило код')


    async def run_single(self):
        if not self.code:
            self.read_code()
        elif(self._runner):
            await self._runner.run_single()


def device_factory(device: Device) -> AbstractSingleRunner:
    if (device.type == DeviceType.INPUT_DEVICE):
        from .input_device import InputDevice
        return InputDevice(device)
    pass
