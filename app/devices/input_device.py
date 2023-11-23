import serial
from app.services import consoleService, Console
from .base_device import BaseDevice

class InputDevice(BaseDevice):

    def __init__(self, serial: serial.Serial, code: str, type: str) -> None:
        super().__init__(serial)
        self.console = consoleService.console(self)
        self.code = code
        self.type = type


    def read_action(self):
        got_str = self.__serial.readline().decode('ascii') #получение отправленных данных
        split = got_str.replace('/n', '').strip().split() #разделяем полученную строку

        if not len(split):
            return False
        if (len(split) != 2):
            self.console.log(f'{self.code} - неверный формат ввода {got_str}')
            return False

        (action_code, payload) = split
        self.console.log(f'DEVICE CODE: {self.code} | ACTION: {action_code} | PAYLOAD: {payload}')


    async def run_single(self):
        super().run_single()

        if self.code:
            self.read_action()