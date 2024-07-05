import sys
import asyncio
import glob
from typing import Dict
import serial
from .console_service import consoleService, Console
from app.devices import Device
from app.model import AbstractRunner


class SerialService(AbstractRunner):
  __search_delays = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4]
  __search_delay_idx = 0
  __devices: Dict[str, Device] = {}

  run_interval = 0.08
  console: Console

  def __init__(self) -> None:
    self.console = consoleService.console(self)
    pass

  def list(self):
    """Lists serial port names

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of the serial ports available on the system
    """

    currentPorts = [*self.__devices.keys()]

    if sys.platform.startswith("win"):
      ports = ["COM%s" % (i + 1) for i in range(256)]
    elif sys.platform.startswith("linux") or sys.platform.startswith("cygwin"):
      # this excludes your current terminal "/dev/tty"
      ports = glob.glob("/dev/tty[A-Za-z]*")
    elif sys.platform.startswith("darwin"):
      ports = glob.glob("/dev/tty.*")
    else:
      raise EnvironmentError("Неподдерживаемая платформа")

    result = []
    for port in ports:
      if port in currentPorts:
        if self.__devices[port].active:
          result.append(port)
          continue
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
        port,  # указание порта
        baudrate=baudrate,  # скорость обмена данными
        parity=serial.PARITY_NONE,  # равенство порта
        stopbits=serial.STOPBITS_ONE,  # размерность байта
        bytesize=serial.EIGHTBITS,  # число бит информации
        timeout=timeout,  # задержка в чтении порта
      )
      self.console.log_self(f"Успешно установлен serial для {port}")
      return ser
    except Exception as _ex:
      self.console.log_self(f"{port} не доступен. Пробуем снова")

    return None

  def install_device(self, port):
    serial = self.define_serial(port)
    if serial:
      self.__devices[port] = Device(serial)

  def delete_device(self, port):
    if self.__devices[port]:
      del self.__devices[port]
      self.console.log_self(f"Порт {port} отключен")

  async def refresh_serials(self):
    currentPorts = [*self.__devices.keys()]

    self.__search_delay_idx = min(self.__search_delay_idx, len(self.__search_delays) - 1)
    await asyncio.sleep(self.__search_delays[self.__search_delay_idx])
    self.__search_delay_idx += 1

    new_ports = self.list()
    if not len(new_ports):
      self.console.log_self("Доступных serial портов не обнаружено")

    for port in new_ports:
      if port in currentPorts:
        continue

      self.install_device(port)

    for port in currentPorts:
      if port not in new_ports:
        self.delete_device(port)

  async def run(self):
    task = asyncio.create_task(self.refresh_serials())

    while True:
      currentDevices = [*self.__devices.values()]
      await asyncio.gather(*[device.run_single() for device in currentDevices])

      if task.done():
        task = asyncio.create_task(self.refresh_serials())

      await asyncio.sleep(self.run_interval)


serialService = SerialService()
__all__ = ["serialService"]
