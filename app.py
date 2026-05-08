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
from flask_mail import Mail  
from flask_dance.contrib.google import make_google_blueprint
from config import config
from models.models import db, User
import os


migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail() 

def create_app(config_name='default'):
    """
    Factory function — creates and configures a Flask application instance.
    Call with 'testing' for unit tests, 'production' for deployment.
    """
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    app = Flask(__name__)

    # ── Load config ────────────────────────────────────────────────
    app.config.from_object(config[config_name])

    # ── Initialise extensions ──────────────────────────────────────
    db.init_app(app)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'ideas'), exist_ok=True)
    migrate.init_app(app, db)       # enables `flask db init/migrate/upgrade`
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)

    # Where Flask-Login redirects unauthenticated users
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # ── User loader (required by Flask-Login) ──────────────────────
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
    
    google_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        scope=["openid", "email", "profile"],
        redirect_to="auth.google_callback",    
    )
    app.register_blueprint(google_bp, url_prefix="/auth")
    csrf.exempt(google_bp)

    # ── Register blueprints ────────────────────────────────────────
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.messages import messages_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(messages_bp)

    return app
