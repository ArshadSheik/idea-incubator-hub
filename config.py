import os
from dotenv import load_dotenv

load_dotenv(override=True)  # reads .env and overrides stale env values


class Config:
    # Security — loaded from environment variable, NEVER hardcoded
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-dev-key-not-for-production'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # suppresses a noisy warning

    # CSRF protection (Flask-WTF)
    WTF_CSRF_ENABLED = True

    # Image-media/Files upload
    UPLOAD_FOLDER      = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'ideas')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024   # 10 MB global Flask request limit

    # mail configuration 
    MAIL_SERVER   = 'smtp.gmail.com'
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = (
        os.environ.get('MAIL_DEFAULT_SENDER')
        or os.environ.get('MAIL_USERNAME')
        or 'noreply@idea-incubator.local'
    )

    GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
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
