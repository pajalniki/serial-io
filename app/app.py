import asyncio
from argparse import Namespace
from .model import SerialIO
from .config import DevelopmentConfig, ProductionConfig

current_app: SerialIO = SerialIO()


def run(args: Namespace):
  # if sys.platform == "win32":
  #   asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

  current_app.args = args
  if args.production:
    current_app.config = ProductionConfig
  else:
    current_app.config = DevelopmentConfig

  try:
    current_app.loop = asyncio.get_event_loop()
    # current_app.loop.set_debug(current_app.config.DEBUG)
    import app.core

    current_app.loop.run_forever()

  except Exception as ex:
    if current_app.loop:
      current_app.loop.stop()
      current_app.loop.close()
    print(f"Сворачиваем приложение... [{ex}]")


__all__ = ["current_app", "run"]
