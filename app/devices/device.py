import asyncio
from multiprocessing import Process
import serial
import time
from reactivex import merge, operators as ops, Observable
from reactivex.disposable.disposable import Disposable
from app.model import SerialIOEvent
from app.services import consoleService, Console
from app.services.socketio_service import socketioService
from app.services.performance_service import performanceService

READ_INTERVAL = 0.01  # нужно считывать как можно чаще, чтобы буффер serial не ждал
# TRANSMIT_INTERVAL = 1  # общее ограничение на чуть больше 10 fps


class Device:
  _serial: serial.Serial
  console: Console
  code: str = None
  subscription: Disposable
  calltime = 0

  @property
  def active(self):
    return self._serial.is_open

  def __init__(self, dev_serial: serial.Serial) -> None:
    self._serial = dev_serial
    self.console = consoleService.console(self)

    input_job = Process(target=self.read_input())
    input_job.start()
    input_job.join()

    transmit_stream: Observable[SerialIOEvent] = socketioService.events.pipe(
      ops.filter(lambda event: self.code and event.device_code == self.code),
      ops.do_action(lambda event: self.transmit_output(event)),
    )

    observables = merge(transmit_stream)

    self.subscription = observables.subscribe()

  def kill(self, ex: Exception = None):
    try:
      self._serial.close()
      self.subscription.dispose()

      if ex:
        self.console.log_self(f"Прерываю устройство {self.code} из-за исключения {ex}")
      else:
        self.console.log_self(f"Прерываю устройство {self.code}")

    except Exception:
      self.console.log_self(f"Прерываю устройство {self.code} [{ex}]")
      return

  def read_code(self):
    got_str = self._serial.readline().decode("ascii")
    code = got_str.replace("/n", "").strip()

    if code:
      self.code = code
      self.console.log_self(f"Устройство {self._serial.port} опознано как {self.code}")
      self._serial.write(str.encode("OK"))
    else:
      self.console.log_self(f"Устройство {self._serial.port} не отправило код")

  # @performanceService.measure_between()
  def get_input(self):
    if not self._serial or not self._serial.in_waiting:
      return
    got_str = self._serial.readline().decode("ascii")  # получение отправленных данных
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
    self._serial.write(str.encode(f"{event.action} {event.payload}"))

  def read_input(self):
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
