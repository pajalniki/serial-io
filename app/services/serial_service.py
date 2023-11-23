import sys
import asyncio
import glob
from typing import Dict
import serial
from .console_service import consoleService, Console
from app.devices import BaseDevice
from app.model import AbstractRunner

class SerialService(AbstractRunner):

    __search_delays = [2, 2, 2, 3, 3, 3, 5, 5, 5, 7]
    __search_delay_idx = 0
    __devices: Dict[str, BaseDevice] = { }

    run_interval = .08
    console: Console


    def __init__(self) -> None:
        self.console = consoleService.console(self)
        pass


    def list(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Неподдерживаемая платформа')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result


    def define_serial(self, port: str, baudrate=9600, timeout=0.1) -> serial.Serial | None:
        try:
            ser = serial.Serial(
                port,                               # указание порта
                baudrate = baudrate,                # скорость обмена данными
                parity=serial.PARITY_NONE,          # равенство порта
                stopbits=serial.STOPBITS_ONE,       # размерность байта
                bytesize=serial.EIGHTBITS,          # число бит информации
                timeout=timeout                     # задержка в чтении порта
            )
            self.console.log(f'Успешно установлен serial для {port}')
            return ser
        except Exception as ex:
            self.console.log(f'{port} не доступен. Пробуем снова')
        
        return None


    def install_device(self, port):
        serial = self.define_serial(port)
        if (serial):
            self.__devices[port] = BaseDevice(serial)

    
    def delete_device(self, port):
        if (self.__devices[port]):
            del self.__devices[port]
            self.console.log(f'Порт {port} отключен')


    async def refresh_serials(self):
        self.__search_delay_idx = min(self.__search_delay_idx, len(self.__search_delays) - 1)
        await asyncio.sleep(self.__search_delays[self.__search_delay_idx])
        self.__search_delay_idx += 1

        new_ports = self.list()
        if not len(new_ports):
            self.console.log('Доступных serial портов не обнаружено')

        for port in new_ports:
            if (port in self.__devices):
                continue

            self.install_device(port)

        for port in self.__devices:
            if not(port in new_ports):
                self.delete_device(port)


    async def run(self):
        while True:
            await asyncio.gather(*[device.run_single() for device in self.__devices.values()],  self.refresh_serials())
            await asyncio.sleep(self.run_interval)


serial_service = SerialService()