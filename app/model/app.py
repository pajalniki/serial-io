from argparse import Namespace
from asyncio import AbstractEventLoop
from app.config import Config

class SerialIO():
    loop: AbstractEventLoop()
    args: Namespace
    config: Config
    
    def __init__(self) -> None:
        pass