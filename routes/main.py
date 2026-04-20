"""
routes/main.py  —  Routes for the main/public-facing pages.

This is YOUR blueprint as the main page developer.
Add new routes here as you wire up more of the frontend.
"""

from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import desc, func

main_bp = Blueprint('main', __name__)

# ─────────────────────────────────────────
# HOME / INDEX  —  the main page you built
# ─────────────────────────────────────────
@main_bp.route('/')
def index():
    return render_template(
        'index.html',
        trending_ideas=[],
        total_users=0,
        total_ideas=0,
    )