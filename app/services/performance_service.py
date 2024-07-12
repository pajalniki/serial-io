import time
from typing import Callable

from app.services.console_service import Console, consoleService


class PerformanceService:
  previousTime = 0
  previousTag = ""
  console: Console

  def __init__(self) -> None:
    self.console = consoleService.console(self)

  def measure_between(self, customTag: str = None):
    def outer(func: Callable):
      tag = customTag or func.__name__

      if tag != self.previousTag:
        self.previousTime = time.perf_counter()
        self.previousTag = tag

      def inner(*args, **kwargs):
        func(*args, **kwargs)
        end = time.perf_counter()
        result = round(end - self.previousTime, 6)
        self.console.log_self(f"[{self.previousTag}]: {result}")
        self.previousTime = end

      return inner

    return outer


performanceService = PerformanceService()
__all__ = ["performanceService"]
