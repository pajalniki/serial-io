from app.model.runner import AbstractSingleRunner
from app.services import Console, consoleService
from .device import Device
from .devices_enums import DeviceType


class InputDevice(AbstractSingleRunner):

    type: DeviceType = DeviceType.INPUT_DEVICE
    console: Console
    _device: Device

    def __init__(self, base: Device) -> None:
        self._device = base
        self.console = consoleService.console(self)

        if (base.type != DeviceType.INPUT_DEVICE):
            raise Exception(f'Неправильный тип устройства ({base.type}) вызвл конструктор {DeviceType.INPUT_DEVICE}')


    def read_action(self):
        from app.services import socketioService
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


    async def run_single(self):
        if (not self._device.active):
            return

        if self._device.code:
            self.read_action()