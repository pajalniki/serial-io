from datetime import datetime

class Console:
    prefix: str

    def __init__(self, prefix) -> None:
        self.prefix = prefix

    def log(self, message: str) -> None:
        time = datetime.now().strftime("%H:%M:%S")

        print(f'[{time}] { self.prefix }:', message)

class ConsoleService:

    def __init__(self) -> None:
        pass

    def console(self, instance) -> Console:
        name = type(instance).__name__
        return Console(name)

consoleService = ConsoleService()

__all__ = ['consoleService', 'Console']