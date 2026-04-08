"""Configuration module for environment-aware settings."""

import os
from dotenv import load_dotenv

# Load local .env for development.
load_dotenv()


class Config:
    """Base configuration with generic defaults."""

    DEBUG = False
    TESTING = False
    INIT_DB = os.getenv("INIT_DB", "false").lower() == "true"
    MONGO_URI = os.getenv("MONGO_URI")
    DB_NAME = os.getenv("DB_NAME") or "vitalai"
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-jwt-secret")
    JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    AUTH_COOKIE_NAME = os.getenv("AUTH_COOKIE_NAME", "vitalai_auth")
    AUTH_COOKIE_MAX_AGE = int(os.getenv("AUTH_COOKIE_MAX_AGE", "86400"))
    AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "Lax")
    AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"


class DevelopmentConfig(Config):
    """Development settings."""

    DEBUG = True
    # Default URI if none provided in .env
    MONGO_URI = os.getenv("MONGO_URI") or "mongodb://localhost:27017/vitalai"


class TestingConfig(Config):
    """Testing settings. No real MongoDB connection should occur."""

    TESTING = True
    INIT_DB = False
    # Safe fallback URI that guarantees isolation
    MONGO_URI = "mongodb://localhost:27017/test_db"
    DB_NAME = "test_db"


class ProductionConfig(Config):
    """Production settings requiring explicit environment variables."""

    DEBUG = False
    # FIX: Do not default MONGO_URI here to force validation failure if absent
    MONGO_URI = os.getenv("MONGO_URI")
    AUTH_COOKIE_SECURE = True


CONFIG_BY_NAME = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env_name=None):
    """Return the configuration class for the given environment."""
    env = (env_name or os.getenv("FLASK_ENV", "production")).lower()
    return CONFIG_BY_NAME.get(env, ProductionConfig)
