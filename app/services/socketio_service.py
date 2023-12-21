import asyncio
import socketio
from typing import Callable, Dict, List
from app import current_app
from app.model import AbstractRunner, SocketioEvent
from app.services.console_service import consoleService, Console

class SocketIOService(AbstractRunner):
    __requests_pool = set()
    __sio = socketio.AsyncSimpleClient()
    __listener: Callable
    __events_recieved: Dict[str, List[SocketioEvent]] = { }
    """
    Словарь полученных событий.
    На одно устройство доступно одно последнее событие для каждого action

    Device_code: { action: payload };
    """

    console: Console
    run_interval = 1.0
    listen_interval = 5

    @property
    def is_connected(self):
        return self.__sio.connected


    def __init__(self) -> None:
        self.console = consoleService.console(self)
        pass


    async def connect(self) -> None:
        await self.__sio.connect(current_app.config.SERVER_HOST)
        
        self.listen()
        self.console.log(f'Подключен к серверу: {current_app.config.SERVER_HOST} (Через {self.__sio.transport()})')


    def listen(self) -> None:
        @self.__sio.client.on('*')
        async def catch_all(event: str, payload: any):
            splitting = event.split(':')

            if (len(splitting) != 2):
                return

            (device_code, action) = splitting
            event_model = SocketioEvent(device_code, action, payload)
            
            self.console.log(f'Событие для устройства {device_code}, действие {action}')

            if not device_code in self.__events_recieved:
                self.__events_recieved[device_code] = [ event_model ]
            else:
                self.__events_recieved[device_code].append(event_model)
                
        self.__listener = catch_all


    def emit_event(self, device_code: str, action: str, payload: any) -> None:
        task = asyncio.create_task(self.__sio.emit(f'{device_code}:{action}', payload))

        # Add task to the set. This creates a strong reference.
        self.__requests_pool.add(task)

        # To prevent keeping references to finished tasks forever,
        # make each task remove its own reference from the set after
        # completion:
        task.add_done_callback(self.__on_event_sent(device_code, action))
        
    
    def transmit_events(self, device_code: str) -> None | List[SocketioEvent]:
        if (device_code not in self.__events_recieved or not self.__events_recieved[device_code]):
            return
        
        copy = [SocketioEvent(e.device_code, e.action, e.payload) for e in self.__events_recieved[device_code]]
        del self.__events_recieved[device_code]
        self.console.log(f'Передал {device_code} {len(copy)} событие(-ий)')
        return copy


    def __on_event_sent(self, device_code: str, action: str):
        def result(task: asyncio.Task):
            self.console.log(f'Отправил событие {action} ({device_code})')
            self.__requests_pool.discard(task)
        return result


    async def run(self):
        task = asyncio.create_task(self.connect())

        while True:
            await asyncio.sleep(self.run_interval)

            if (self.is_connected):
                continue
            
            if (not task):
                task = asyncio.create_task(self.connect())
                continue

            if (task.cancelled() or (task.done() and task.exception()) or (task.done() and not self.is_connected)):
                self.console.log(f'Возникли проблемы с подключением к {current_app.config.SERVER_HOST}. Пробую снова')
                task = asyncio.create_task(self.connect())


socketioService = SocketIOService()
__all__ = ['socketioService']
