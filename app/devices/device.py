import serial
from app.model import AbstractSingleRunner
from app.services import consoleService, Console, socketioService
from .devices_enums import DeviceType

class Device(AbstractSingleRunner):
    _serial: serial.Serial
    console: Console
    code: str = None
    type: DeviceType = None
    
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


    def get_input(self):
        try:
            got_str = self._device._serial.readline().decode('ascii') #получение отправленных данных
            split = got_str.replace('/n', '').strip().split() #разделяем полученную строку

            if not len(split):
                return
            if (len(split) != 2):
                self.console.log(f'{self._device.code} - неверный формат ввода {got_str}')
                return

            (action_code, payload) = split
            self.console.log(f'КОД: {self._device.code} | СОБЫТИЕ: {action_code} | ДАННЫЕ: {payload}')
            
            if (not socketioService.is_connected):
                self.console.log(f'Связь с сервером недоступна')
                return
            
            socketioService.emit_event(self._device.code, action_code, payload)

        except Exception as ex:
            self.console.log(f'{self._device.code} - выполнение прервано. {ex}')
            self.console.log(f'Отключаю {self._device.code}')
            self._device.kill()
            return
        

    async def send_output(self):
        pass


    async def run_single(self):
        if not self.code:
            self.read_code()
            return
        
        if (self.type == DeviceType.INPUT_DEVICE or self.type == DeviceType.INPUT_OUTPUT_DEVICE):
            self.get_input()
            
        if (self.type == DeviceType.OUTPUT_DEVICE or self.type == DeviceType.INPUT_OUTPUT_DEVICE):
            self.send_output()


def device_factory(device: Device) -> AbstractSingleRunner:
    if (device.type == DeviceType.INPUT_DEVICE):
        from .input_device import InputDevice
        return InputDevice(device)
    pass
