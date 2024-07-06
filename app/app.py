from argparse import Namespace
import asyncio

from .model import SerialIO
from .config import DevelopmentConfig, ProductionConfig

current_app: SerialIO = SerialIO()


def run(args: Namespace):
  from .services import serialService, socketioService

  current_app.args = args
  current_app.loop = asyncio.get_event_loop()

  if args.production:
    current_app.config = ProductionConfig
  else:
    current_app.config = DevelopmentConfig

  try:
    asyncio.ensure_future(socketioService.run())
    current_app.loop.run_forever()
  except KeyboardInterrupt:
    current_app.loop.stop()
  finally:
    print("Сворачиваем приложение...")
    current_app.loop.close()


__all__ = ["current_app", "run"]
