import os
import secrets


def bool_env(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def int_env(name, default, minimum=None, maximum=None):
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


class Settings:
    APP_NAME = "ORION Legacy Edition"
    VERSION = "Legacy Edition"
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    IS_PRODUCTION = FLASK_ENV == "production"
    AUTH_REQUIRED = bool_env("AUTH_REQUIRED", False)
    ORION_USERNAME = os.getenv("ORION_USERNAME", "").strip()
    ORION_PASSWORD = os.getenv("ORION_PASSWORD", "").strip()
    SESSION_DAYS = int_env("SESSION_DAYS", 14, minimum=1, maximum=30)
    MAX_MESSAGE_LENGTH = int_env("MAX_MESSAGE_LENGTH", 1000, minimum=80, maximum=4000)
    MAX_CONTENT_LENGTH = int_env("MAX_CONTENT_LENGTH", 16 * 1024, minimum=1024, maximum=256 * 1024)
    RATE_LIMIT = "30 per minute"
    RATE_LIMIT_MAX_REQUESTS = int_env("RATE_LIMIT_MAX_REQUESTS", 30, minimum=5, maximum=120)
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    CORS_ORIGINS = [origin.strip() for origin in os.getenv("ORION_CORS_ORIGINS", "").split(",") if origin.strip()]
