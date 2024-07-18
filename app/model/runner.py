from abc import ABC, abstractmethod


class AbstractRunner(ABC):
  @abstractmethod
  async def on_refresh_fail(self):
    pass


class AbstractSingleRunner(ABC):
  @abstractmethod
  async def run_single(self):
    pass
