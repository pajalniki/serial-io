import asyncio
import multiprocessing
import socketio
from reactivex import Observable, Subject, operators as ops
from reactivex.disposable.disposable import Disposable
from reactivex.scheduler.eventloop import AsyncIOScheduler
from typing import Callable
from app import current_app
from app.model import AbstractRunner, SerialIOEvent
from .console_service import consoleService, Console


class SocketIOService(AbstractRunner):
  __requests_pool = set()
  __sio = socketio.AsyncSimpleClient()
  __listener: Callable
  __events_subject: Subject[SerialIOEvent] = Subject()
  __subscription: Disposable

  events: Observable[SerialIOEvent]

  console: Console
  run_interval = 1.0
  listen_interval = 5

  @property
  def is_connected(self):
    return self.__sio.connected

  def __init__(self) -> None:
    self.console = consoleService.console(self)
    loop = asyncio.new_event_loop()
    scheduler = AsyncIOScheduler(loop)

    self.events = self.__events_subject.pipe(
      ops.observe_on(scheduler),
    )

    self.__subscription = self.events.subscribe()

  async def connect(self) -> None:
    await self.__sio.connect(current_app.config.SERVER_HOST)

    self.listen()
    self.console.log_self(f"Подключен к серверу: {current_app.config.SERVER_HOST} (Через {self.__sio.transport()})")

  def listen(self) -> None:
    @self.__sio.client.on("*")
    async def catch_all(event: str, payload: any):
      splitting = event.split(":")

      if len(splitting) != 2:
        return

      (device_code, action) = splitting
      event_model = SerialIOEvent(device_code, action, payload)

      # self.console.log_self(f"Событие для устройства {device_code}, действие {action}")
      self.__events_subject.on_next(event_model)

    self.__listener = catch_all

  def emit_event(self, event: SerialIOEvent) -> None:
    task = current_app.loop.create_task(self.__sio.emit(f"{event.device_code}:{event.action}", event.payload))

    # Add task to the set. This creates a strong reference.
    self.__requests_pool.add(task)

    # To prevent keeping references to finished tasks forever,
    # make each task remove its own reference from the set after
    # completion:
    task.add_done_callback(lambda _task: self.__requests_pool.discard(_task))

  async def run(self):
    task = asyncio.create_task(self.connect())

    while True:
      await asyncio.sleep(self.run_interval)

      if self.is_connected:
        continue

      if not task:
        task = asyncio.create_task(self.connect())
        continue

      if task.cancelled() or (task.done() and task.exception()) or (task.done() and not self.is_connected):
        self.console.log_self(f"Возникли проблемы с подключением к {current_app.config.SERVER_HOST}. Пробую снова")
        task = asyncio.create_task(self.connect())


socketioService = SocketIOService()
__all__ = ["socketioService"]
