import os
import sys


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

    # In production, ensure MONGO_URI comes from environment (but skip in pytest)
    if name.lower() == "production" and "pytest" not in sys.modules:
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise ValueError(
                "MONGO_URI environment variable is required for production deployment. "
                "Set it in your Render.com environment variables."
            )

    return config
