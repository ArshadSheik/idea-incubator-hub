"""
extensions.py — Flask extension singletons.

Defined here (not in app.py) so blueprints can import them without
creating circular imports.  app.py calls .init_app(app) on each one
inside create_app().
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# In-memory storage is fine for dev/single-process deployments.
# Swap storage_uri to "redis://..." for multi-worker production.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],          # no blanket limit; only apply where decorated
    storage_uri="memory://",
)
