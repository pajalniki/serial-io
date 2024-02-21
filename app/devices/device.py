import asyncio
import serial
from app.model import AbstractSingleRunner
from app.services import consoleService, Console
from app.services.socketio_service import socketioService

string_encode_interval = 0.02

class Device(AbstractSingleRunner):
    _serial: serial.Serial
    console: Console
    code: str = None
    
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
        
        if (code):
            self.code = code
            self.console.log(f'Устройство {self._serial.port} опознано как {self.code}')
            self._serial.write(str.encode('OK'))
        else:
            self.console.log(f'Устройство {self._serial.port} не отправило код')


    def get_input(self):
        try:
            got_str = self._serial.readline().decode('ascii') #получение отправленных данных
            split = got_str.replace('/n', '').strip().split() #разделяем полученную строку

            if not len(split):
                return
            if (len(split) != 2):
                self.console.log(f'{self.code} - неверный формат ввода {got_str}')
                return

            (action_code, payload) = split
            self.console.log(f'КОД: {self.code} | СОБЫТИЕ: {action_code} | ДАННЫЕ: {payload}')
            
            if (not socketioService.is_connected):
                self.console.log(f'Связь с сервером недоступна')
                return
            
            socketioService.emit_event(self.code, action_code, payload)

        except Exception as ex:
            self.console.log(f'{self.code} - выполнение прервано. {ex}')
            self.console.log(f'Отключаю {self.code}')
            self.kill()
            return
        

    async def transmit_output(self):
        events = socketioService.transmit_events(self.code)
        if (not events or not len(events)):
            return
        
        # Важный момент, имя устройства не передаем. Сокращаем количество передаваемых данных
        for event in events:
            self._serial.write(str.encode(f'{event.action} {event.payload}'))
            await asyncio.sleep(string_encode_interval)
            pass


    async def run_single(self):
        if not self.active:
            return

        if not self.code:
            self.read_code()
            return
        
        self.get_input()
        
        await self.transmit_output()