from flask import Blueprint, redirect, render_template, url_for

from models.models import Comment, Idea, User

main_bp = Blueprint("main", __name__)


@main_bp.app_errorhandler(404)
def page_not_found(_error):
    return render_template("404.html"), 404


# ─────────────────────────────────────────
# Landing page
# ─────────────────────────────────────────
@main_bp.route("/")
def index():
    # Show the 6 most recent public ideas in the trending grid
    trending_ideas = (
        Idea.query
        .filter_by(privacy='public')
        .order_by(Idea.created_at.desc())
        .limit(6)
        .all()
    )
    total_ideas    = Idea.query.filter_by(privacy='public').count()
    total_users    = User.query.count()
    total_comments = Comment.query.count()

    return render_template(
        "index.html",
        trending_ideas=trending_ideas,
        total_ideas=total_ideas,
        total_users=total_users,
        total_comments=total_comments,
    )


# ─────────────────────────────────────────
# Render-only shells for pages owned elsewhere.
# These keep the app booting end-to-end while each page is built out.
# ─────────────────────────────────────────
@main_bp.route("/explore")
def explore():
    return render_template("explore.html", ideas=[])


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/ideas/<int:idea_id>")
def idea_detail(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    return render_template("idea_detail.html", idea=idea)


@main_bp.route("/login")
def login():
    return render_template("login.html")


@main_bp.route("/register")
def register():
    return render_template("register.html")


# ─────────────────────────────────────────
# Legacy .html redirects
# ─────────────────────────────────────────
@main_bp.route("/index.html")
def index_html():
    return redirect(url_for("main.index"))


@main_bp.route("/explore.html")
def explore_html():
    return redirect(url_for("main.explore"))


@main_bp.route("/dashboard.html")
def dashboard_html():
    return redirect(url_for("main.dashboard"))


@main_bp.route("/login.html")
def login_html():
    return redirect(url_for("main.login"))


@main_bp.route("/register.html")
def register_html():
    return redirect(url_for("main.register"))