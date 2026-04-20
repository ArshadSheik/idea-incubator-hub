"""
app.py  —  Application factory for Idea Incubator Hub.

Using the application factory pattern means:
  - Tests can spin up a fresh app with TestingConfig (in-memory DB, CSRF off)
  - No circular imports between models, routes, and the app object
"""

from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config
from models.models import db, User


migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name='default'):
    """
    Factory function — creates and configures a Flask application instance.
    Call with 'testing' for unit tests, 'production' for deployment.
    """
    app = Flask(__name__)

    # ── Load config ────────────────────────────────────────────────
    app.config.from_object(config[config_name])

    # ── Initialise extensions ──────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)       # enables `flask db init/migrate/upgrade`
    login_manager.init_app(app)
    csrf.init_app(app)

    # Where Flask-Login redirects unauthenticated users
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # ── User loader (required by Flask-Login) ──────────────────────
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Register blueprints ────────────────────────────────────────
    from routes.main import main_bp
    #from routes.auth import auth_bp

    app.register_blueprint(main_bp)
    #app.register_blueprint(auth_bp, url_prefix='/auth')

    return app
