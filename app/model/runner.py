from abc import ABC, abstractmethod


class AbstractRunner(ABC):
  @abstractmethod
  async def run(self):
    pass


class AbstractSingleRunner(ABC):
  @abstractmethod
  async def run_single(self):
    pass
