import logging
import os
import sys

from dotenv import load_dotenv

# Load .env early so config reads environment values during import
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    DEBUG = False
    TESTING = False
    # Only initialize DB when explicitly enabled via environment variable
    # GitHub Actions smoke test: defaults to False (no MongoDB required)
    # Render.com deployment: set INIT_DB=true with MongoDB Atlas URI
    # Local development: set INIT_DB=true if MongoDB is running
    INIT_DB = os.getenv("INIT_DB", "false").lower() == "true"
    # MongoDB Atlas URI should be provided via MONGO_URI environment variable
    # Falls back to localhost only for local development
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/vitalai")
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret")
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    INIT_DB = False


class ProductionConfig(Config):
    DEBUG = False
    # INIT_DB is inherited from Config - uses environment variable or defaults to false


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name=None):
    if not name:
        # Default to production for safety; only use development in dev environments
        name = os.getenv("FLASK_ENV", "production")
    config = CONFIG_BY_NAME.get(name.lower(), ProductionConfig)

    # Ensure a safe default if MONGO_URI is unset/blank (helps smoke tests)
    import os

    from dotenv import load_dotenv


    class Config:
        """Base config with defaults populated from environment variables."""

        DEBUG = False
        TESTING = False
        MONGO_URI = os.getenv("MONGO_URI")
        DB_NAME = os.getenv("DB_NAME")
        JWT_SECRET = os.getenv("JWT_SECRET")
        JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))


    class DevelopmentConfig(Config):
        """Development config loads settings from .env via python-dotenv."""

        DEBUG = True


    class TestingConfig(Config):
        """Testing config never touches a real MongoDB instance."""

        TESTING = True
        MONGO_URI = "mongodb://localhost:27017/test_db"
        DB_NAME = "test_db"


    class ProductionConfig(Config):
        """Production config relies entirely on environment variables."""

        DEBUG = False


    def _apply_env(config_cls: type[Config]) -> type[Config]:
        """Refresh config values from environment after loading .env."""

        config_cls.MONGO_URI = os.getenv("MONGO_URI")
        config_cls.DB_NAME = os.getenv("DB_NAME")
        config_cls.JWT_SECRET = os.getenv("JWT_SECRET")
        config_cls.JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
        return config_cls


    def get_config(env_name: str | None = None) -> type[Config]:
        """Return the config class based on FLASK_ENV."""

        env = (env_name or os.getenv("FLASK_ENV", "development")).lower()

        if env == "development":
            # Load .env only for development to avoid overriding Render env vars.
            load_dotenv()
            return _apply_env(DevelopmentConfig)

        if env == "testing":
            return TestingConfig

        if env == "production":
            if not os.getenv("MONGO_URI"):
                raise EnvironmentError(
                    "MONGO_URI environment variable is required for production."
                )
            return _apply_env(ProductionConfig)

        return _apply_env(DevelopmentConfig)
