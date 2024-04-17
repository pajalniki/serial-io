from datetime import datetime

class Console:
    prefix: str

    def __init__(self, prefix) -> None:
        self.prefix = prefix
        self.previousPhrase = ""

    def log_hard(self, message: str) -> None:
        '''Выводит сообщение в консоль немедленно'''
        time = datetime.now().strftime("%H:%M:%S")
        print(f'[{time}] { self.prefix }:', message)
        self.previousPhrase = message

    def log_self(self, message: str):
        '''Выводит сообщение в консоль только в случае, если оно отличается от прошлого сообщения консоли'''
        if self.previousPhrase != message:
            self.log_hard(message)
        self.previousPhrase = message



class ConsoleService:

    def __init__(self) -> None:
        pass

    def console(self, instance) -> Console:
        name = type(instance).__name__
        return Console(name)

consoleService = ConsoleService()

__all__ = ['consoleService', 'Console']