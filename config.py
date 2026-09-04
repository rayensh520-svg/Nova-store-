import os


class Config:
    SECRET_KEY = os.environ.get(
        "NOVA_SECRET_KEY",
        "nova-development-secret-key"
    )

    APP_NAME = "NOVA STORE"

    ENVIRONMENT = os.environ.get(
        "NOVA_ENVIRONMENT",
        "development"
    )

    DEBUG = ENVIRONMENT == "development"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = ENVIRONMENT == "production"

    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
