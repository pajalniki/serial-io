"""
Конфиг Serial IO
Обратите внимание на различные конфигурации для linux и windows
"""

class Config(object):
    TESTING = False

class WindowsConfig(Config):
    DEBUG = False
    FLASK_ENV = 'production'

class LinuxConfig(Config):
    DEBUG = True
    FLASK_ENV = 'development'
    ENV = "development"

class TestingConfig(Config):
    TESTING = True