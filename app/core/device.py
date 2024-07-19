from concurrent.futures import Executor, ThreadPoolExecutor
import serial
import time
from reactivex import operators as ops, Observable
from reactivex.disposable.disposable import Disposable
from app.model import SerialIOEvent
from app.shared import consoleService, Console
from app.core.socketio_service import socketioService

READ_INTERVAL = 0.01  # трамплин


class Device:
  __serial: serial.Serial
  __subscription: Disposable
  __executor: Executor

  console: Console
  code: str = None

  @property
  def active(self):
    return self.__serial.is_open

  def __init__(self, dev_serial: serial.Serial) -> None:
    self.__serial = dev_serial
    self.console = consoleService.console(self)
    self.__executor = ThreadPoolExecutor(max_workers=1)
    self.__executor.submit(self.run_thread)

    transmit_stream: Observable[SerialIOEvent] = socketioService.transmit.pipe(
      ops.filter(lambda event: self.code and event.device_code == self.code),
      ops.do_action(lambda event: self.transmit_output(event)),
    )

    self.__subscription = transmit_stream.subscribe()

  def kill(self, ex: Exception = None):
    try:
      self.__serial.close()
      self.__subscription.dispose()
      self.__executor.shutdown(wait=False, cancel_futures=True)

    finally:
      self.console.log_self(f"Прерываю устройство {self.code} [{ex}]")
      return

  def read_code(self):
    if not self.__serial or not self.__serial.in_waiting:
      return

    got_str = self.__serial.readline().decode("ascii")
    code = got_str.replace("/n", "").strip()

    if code:
      self.code = code
      self.console.log_self(f"Устройство {self.__serial.port} опознано как {self.code}")
      self.__serial.write(str.encode("OK"))
    else:
      self.console.log_self(f"Устройство {self.__serial.port} не отправило код")

  # @performanceService.measure_between()
  def get_input(self):
    if not self.__serial or not self.__serial.in_waiting:
      return
    got_str = self.__serial.readline().decode("ascii")  # получение отправленных данных
    split = got_str.replace("/n", "").strip().split()  # разделяем полученную строку

    if not split:
      return
    if len(split) != 2:
      self.console.log_self(f"{self.code} - неверный формат ввода {got_str}")
      return

    (action_code, payload) = split
    # self.console.log_self(f"КОД: {self.code} | СОБЫТИЕ: {action_code} | ДАННЫЕ: {payload}")

    if not socketioService.is_connected:
      self.console.log_self("Связь с сервером недоступна")
      return

    socketioService.emit_event(SerialIOEvent(self.code, action_code, payload))

  def transmit_output(self, event: SerialIOEvent):
    self.__serial.write(str.encode(f"{event.action} {event.payload}"))

  def run_thread(self):
    try:
      while True:
        if not self.code:
          self.read_code()
        else:
          self.get_input()
        time.sleep(READ_INTERVAL)

    except Exception as ex:
      self.kill(ex)
      return
