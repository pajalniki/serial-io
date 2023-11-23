import asyncio
from .services import serial_service

def run():
    loop = asyncio.get_event_loop()
    try:
        asyncio.ensure_future(serial_service.run())
        loop.run_forever()
    except KeyboardInterrupt:
        loop.stop()
    finally:
        print("Сворачиваем приложение...")
        loop.close()