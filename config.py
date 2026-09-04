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
