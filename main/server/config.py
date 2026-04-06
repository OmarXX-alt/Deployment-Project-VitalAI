import os


class Config:
    DEBUG = False
    TESTING = False
    INIT_DB = True
    MONGO_URI = os.getenv("MONGO_URI")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    INIT_DB = False


class ProductionConfig(Config):
    DEBUG = False
    INIT_DB = False


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    if not name:
        name = os.getenv("FLASK_ENV", "production")
    return CONFIG_BY_NAME.get(name.lower(), ProductionConfig)
