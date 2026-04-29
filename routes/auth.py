# routes/auth.py
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
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