import os
from dotenv import load_dotenv

load_dotenv()  # reads .env file


class Config:
    # Security — loaded from environment variable, NEVER hardcoded
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-dev-key-not-for-production'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # suppresses a noisy warning

    # CSRF protection (Flask-WTF)
    WTF_CSRF_ENABLED = True


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # in-memory DB for tests
    WTF_CSRF_ENABLED = False                        # easier form testing


class ProductionConfig(Config):
    DEBUG = False


# Map string names to config classes — used in app factory
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
