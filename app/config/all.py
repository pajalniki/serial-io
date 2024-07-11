"""
Конфиг Serial IO
Обратите внимание на различные конфигурации тестового и боевого режима
"""


class Config(object):
  DEBUG = True
  SERVER_HOST = "http://127.0.0.1:5000"
  SERIAL_BAUD = 9600


class ProductionConfig(Config):
  DEBUG = False
  SERVER_HOST = "http://172.20.128.2:5555"


class DevelopmentConfig(Config):
  DEBUG = True
  SERVER_HOST = "http://127.0.0.1:5000"
