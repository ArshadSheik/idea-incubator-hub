"""
app.py  —  Application factory for Idea Incubator Hub.

Using the application factory pattern means:
  - Tests can spin up a fresh app with TestingConfig (in-memory DB, CSRF off)
  - No circular imports between models, routes, and the app object
"""

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

from config import config

csrf = CSRFProtect()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    csrf.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return None        # ← returns None for now, real query added in commit 2

    from routes.main import main_bp
    app.register_blueprint(main_bp)

    return app