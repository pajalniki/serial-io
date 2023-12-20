import asyncio
import socketio
from app import current_app
from app.model import AbstractRunner
from .console_service import consoleService, Console

class SocketIOService(AbstractRunner):
    __requests_pool = set()
    __sio = socketio.AsyncSimpleClient()

    console: Console
    run_interval = 1.0


    @property
    def is_connected(self):
        return self.__sio.connected


    def __init__(self) -> None:
        self.console = consoleService.console(self)
        pass


    async def connect(self) -> None:
        await self.__sio.connect(current_app.config.SERVER_HOST)
        self.console.log(f'Подключен к серверу: {current_app.config.SERVER_HOST}')


    def emit_event(self, device_code: str, action: str, payload: any) -> None:
        task = asyncio.create_task(self.__sio.emit(f'{device_code}:{action}', payload))

        # Add task to the set. This creates a strong reference.
        self.__requests_pool.add(task)

        # To prevent keeping references to finished tasks forever,
        # make each task remove its own reference from the set after
        # completion:
        task.add_done_callback(self.__make_done_callback(device_code, action))


    def __make_done_callback(self, device_code: str, action: str):
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
