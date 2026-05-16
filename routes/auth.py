# routes/auth.py
import random
import re
from urllib.parse import urljoin, urlparse
from flask_dance.contrib.google import google
from flask import Blueprint, flash, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash

from extensions import limiter
from models.models import User, db

auth_bp = Blueprint("auth", __name__)

_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _is_safe_redirect(target: str) -> bool:
    if not target:
        return False
    host_url = request.host_url
    test_url = urlparse(urljoin(host_url, target))
    ref_url = urlparse(host_url)
    return test_url.scheme in {"http", "https"} and ref_url.netloc == test_url.netloc


# ─────────────────────────────────────────
# register
# ─────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # if logined , go to main.index directly
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        first_name       = request.form.get("first_name", "").strip()
        last_name        = request.form.get("last_name", "").strip()
        username         = request.form.get("username", "").strip()
        email            = request.form.get("email", "").strip().lower()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # ── verify ──────────────────────────────────────────────────
        if not all([first_name, last_name, username, email, password]):
            flash("All fields are required.")
            return render_template("register.html")

        if not _EMAIL_RE.match(email):
            flash("Please enter a valid email address.")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("That username is already taken.")
            return render_template("register.html")

        # ── create user ──────────────────────────────────────────────
        user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for("main.dashboard"))

    return render_template("register.html")


# ─────────────────────────────────────────
# login
# ─────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("15 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    next_page = request.args.get("next") or request.form.get("next") or ""
    if not next_page:
        referrer = request.referrer or ""
        if _is_safe_redirect(referrer):
            next_page = referrer
    if request.method == "POST":
        login_input = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"
        
        user = User.query.filter_by(email=login_input.lower()).first()
        if user is None:
            user = User.query.filter_by(username=login_input).first()

        if user is None or not user.check_password(password):
            flash("Incorrect email or password.")
            return render_template("login.html", next_page=next_page)

        login_user(user, remember=remember)

        if next_page and _is_safe_redirect(next_page):
            return redirect(next_page)
        return redirect(url_for("main.dashboard"))

    return render_template("login.html", next_page=next_page)


# ─────────────────────────────────────────
# logout
# ─────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

def _get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

def generate_reset_token(email: str) -> str:
    return _get_serializer().dumps(email, salt='password-reset')

def verify_reset_token(token: str, max_age: int = 3600):
    try:
        email = _get_serializer().loads(token, salt='password-reset', max_age=max_age)
    except (SignatureExpired, BadSignature):
        return None
    return email


def _mail_sender():
    return current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')


def _mail_configured():
    return bool(
        current_app.config.get('MAIL_USERNAME')
        and current_app.config.get('MAIL_PASSWORD')
        and _mail_sender()
    )


def _send_password_reset_email(user: User, reset_url: str) -> None:
    from app import mail

    body = f"""Hi {user.first_name},

You requested a password reset. Click the link below to set a new password:

{reset_url}

This link expires in 1 hour. If you didn't request this, you can safely ignore this email.

— Idea Incubator Hub
"""
    if not _mail_configured():
        if current_app.debug:
            current_app.logger.info('MAIL not configured (dev skips email; user redirected to reset form).')
        else:
            current_app.logger.error(
                'Password reset requested but mail is not configured (set MAIL_USERNAME and MAIL_PASSWORD).'
            )
        return

    msg = Message(
        subject='Reset your Idea Incubator password',
        recipients=[user.email],
        sender=_mail_sender(),
        body=body,
    )
    mail.send(msg)


# ─────────────────────────────────────────
# Step 1：input email , send reset mail
# ─────────────────────────────────────────
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not _EMAIL_RE.match(email):
            flash("If that email is registered, you'll receive a reset link shortly.")
            return redirect(url_for("auth.forgot_password"))

        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_reset_token(user.email)
            # Local dev without SMTP: go straight to the reset form (no terminal copy-paste)
            if current_app.debug and not _mail_configured():
                return redirect(url_for("auth.reset_password", token=token))
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            _send_password_reset_email(user, reset_url)
            flash("If that email is registered, you'll receive a reset link shortly.")
        elif current_app.debug:
            flash("No account with that email. Use the address you registered with.")
        else:
            flash("If that email is registered, you'll receive a reset link shortly.")

        return redirect(url_for("auth.forgot_password"))

    return render_template("forgot_password.html")


# ─────────────────────────────────────────
# Step input new password
# ─────────────────────────────────────────
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    email = verify_reset_token(token)
    if email is None:
        flash("This reset link is invalid or has expired. Please request a new one.")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 8:
            flash("Password must be at least 8 characters.")
            return render_template("reset_password.html", token=token)

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("reset_password.html", token=token)

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found.")
            return redirect(url_for("auth.forgot_password"))

        user.set_password(password)
        db.session.commit()

        flash("Password updated! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)

@auth_bp.route("/google/callback")
def google_callback():
    if not google.authorized:
        flash("Google login was cancelled.")
        return redirect(url_for("auth.login"))

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google. Please try again.")
        return redirect(url_for("auth.login"))

    info       = resp.json()
    google_email = info["email"].lower()
    first_name   = info.get("given_name", "")
    last_name    = info.get("family_name", "")
    user = User.query.filter_by(email=google_email).first()

    if user is None:
        base_username = google_email.split("@")[0][:20]
        username = base_username
        if User.query.filter_by(username=username).first():
            username = f"{base_username[:15]}{random.randint(100, 999)}"

        user = User(
            email        = google_email,
            username     = username,
            first_name   = first_name or base_username,
            last_name    = last_name  or "",
            avatar_color = random.randint(1, 6),
        )
        user.set_password(f"google-oauth-{random.randbytes(16).hex()}")
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for("main.dashboard"))
