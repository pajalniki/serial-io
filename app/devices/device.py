import serial
from reactivex import interval, merge, operators as ops, Observable
from reactivex.disposable.disposable import Disposable
from reactivex.abc import SchedulerBase
from app.services import consoleService, Console
from app.services.socketio_service import socketioService

READ_INTERVAL = 0.01  # нужно считывать как можно чаще, чтобы буффер serial не ждал
TRANSMIT_INTERVAL = 0.095  # общее ограничение на чуть больше 10 fps


class Device:
  _serial: serial.Serial
  console: Console
  code: str = None
  subscription: Disposable

  @property
  def active(self):
    return self._serial.is_open

  def __init__(self, dev_serial: serial.Serial, sheduler: SchedulerBase) -> None:
    self._serial = dev_serial
    self.console = consoleService.console(self)

    readStream: Observable = interval(READ_INTERVAL).pipe(
      ops.observe_on(sheduler),
      ops.filter(lambda _n: self.active),
      ops.map(lambda _n: self.read_input()),
      ops.catch(lambda ex, _obs: self.kill(ex)),
    )

    transmitStream: Observable = interval(TRANSMIT_INTERVAL).pipe(
      ops.observe_on(sheduler),
      ops.filter(lambda _n: self.active),
      ops.map(lambda _n: self.transmit_output()),
      ops.catch(lambda ex, _obs: self.kill(ex)),
    )

    observables: Observable = merge(readStream, transmitStream)

    self.subscription = observables.subscribe()

  def kill(self, ex: Exception):
    self._serial.close()
    self.subscription.dispose()
    if ex:
      self.console.log_self(f"Прерываю устройство {self.code} из-за исключения {ex}")
    else:
      self.console.log_self(f"Прерываю устройство {self.code}")
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

  def get_input(self):
    if not self._serial or not self._serial.in_waiting:
      return

    try:
      got_str = self._serial.readline().decode("ascii")  # получение отправленных данных
      split = got_str.replace("/n", "").strip().split()  # разделяем полученную строку

      if not split:
        return
      if len(split) != 2:
        self.console.log_self(f"{self.code} - неверный формат ввода {got_str}")
        return

      (action_code, payload) = split
      self.console.log_self(f"КОД: {self.code} | СОБЫТИЕ: {action_code} | ДАННЫЕ: {payload}")

      if not socketioService.is_connected:
        self.console.log_self("Связь с сервером недоступна")
        return

      socketioService.emit_event(self.code, action_code, payload)

    except Exception as ex:
      self.console.log_self(f"{self.code} - выполнение прервано. {ex} \nОтключаю {self.code}")
      self.kill()
      return

  def transmit_output(self):
    events = socketioService.transmit_events(self.code)
    if not events or not len(events):
      return

    # Важный момент, имя устройства не передаем. Сокращаем количество передаваемых данных
    for event in events:
      self._serial.write(str.encode(f"{event.action} {event.payload}"))

  def read_input(self):
    if not self.code:
      self.read_code()
      return

    self.get_input()
