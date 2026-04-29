# routes/auth.py
from flask import Blueprint, flash, redirect, render_template, request, url_for,current_app
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash

from models.models import User, db

auth_bp = Blueprint("auth", __name__)


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
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash("Incorrect email or password.")
            return render_template("login.html")

        login_user(user, remember=remember)

        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.dashboard"))

    return render_template("login.html")


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

# ─────────────────────────────────────────
# Step 1：input email , send reset mail
# ─────────────────────────────────────────
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            from app import mail
            msg = Message(
                subject="Reset your Idea Incubator password",
                recipients=[user.email],
            )
            msg.body = f"""Hi {user.first_name},

You requested a password reset. Click the link below to set a new password:

{reset_url}

This link expires in 1 hour. If you didn't request this, you can safely ignore this email.

— Idea Incubator Hub
"""
            mail.send(msg)

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

        flash("Password updated! You can now log in.")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", token=token)
