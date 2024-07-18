import asyncio
from concurrent.futures import ThreadPoolExecutor
import socketio
from reactivex import Observable, Subject, from_future, interval, merge, operators as ops
from reactivex.scheduler.eventloop import AsyncIOScheduler
from app import current_app
from app.model import SerialIOEvent
from app.shared import consoleService, Console

REFRESH_INTERVAL = 1.5


class SocketIOService:
  __sio = socketio.AsyncSimpleClient()
  __transmit_subject: Subject[SerialIOEvent] = Subject()
  __send: Observable[SerialIOEvent]
  __executor = ThreadPoolExecutor

  send_subj: Subject[SerialIOEvent] = Subject()
  transmit: Observable[SerialIOEvent]

  console: Console

  @property
  def is_connected(self):
    return self.__sio.connected

  def __init__(self) -> None:
    self.console = consoleService.console(self)

    asyncio.set_event_loop(current_app.loop)

    self.transmit = self.__transmit_subject.pipe(ops.filter(lambda _n: self.is_connected))

    refresh = interval(REFRESH_INTERVAL).pipe(
      ops.filter(lambda _n: not self.is_connected),
      ops.do_action(lambda _n: from_future(asyncio.ensure_future(self.connect()))),
    )

    observables = merge(refresh, self.transmit)

    # подписка на send происходит в отдельном потоке
    observables.subscribe(scheduler=AsyncIOScheduler(current_app.loop))

    self.__executor = ThreadPoolExecutor(max_workers=1)
    self.__executor.submit(self.separate_send_thread)

  async def connect(self) -> None:
    try:
      await self.__sio.connect(current_app.config.SERVER_HOST)
      self.listen()
      self.console.log_self(f"Подключен к серверу: {current_app.config.SERVER_HOST} (Через {self.__sio.transport()})")

    except Exception:
      self.console.log_self(f"Возникли проблемы с подключением к {current_app.config.SERVER_HOST}. Пробую снова")

  def listen(self) -> None:
    @self.__sio.client.on("*")
    async def catch_all(event: str, payload: any):
      splitting = event.split(":")

      if len(splitting) != 2:
        return

      (device_code, action) = splitting
      event_model = SerialIOEvent(device_code, action, payload)

      # self.console.log_self(f"Событие для устройства {device_code}, действие {action}")
      self.__transmit_subject.on_next(event_model)

    self.__listener = catch_all

  def separate_send_thread(self):
    thread_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(thread_loop)

  def emit_event(self, event: SerialIOEvent):
    self.__executor.submit(self.emit_event_in_thread, event)

  def emit_event_in_thread(self, event: SerialIOEvent):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(self.__sio.emit(f"{event.device_code}:{event.action}", event.payload))


socketioService = SocketIOService()
__all__ = ["socketioService"]
