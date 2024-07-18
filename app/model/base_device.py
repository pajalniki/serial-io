import serial
from abc import ABC, abstractmethod


class DeviceBase(ABC):
  @abstractmethod
  def kill(ex: Exception):
    pass

  def __init__(self, dev_serial: serial.Serial) -> None:
    pass
