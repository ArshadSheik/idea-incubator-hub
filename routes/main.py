from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for

from models.models import Collaboration, Comment, Idea, User

main_bp = Blueprint("main", __name__)


CATEGORY_TAG_CLASS = {
    "FinTech": "tag-brand",
    "EdTech": "tag-violet",
    "GreenTech": "tag-mint",
    "DevTools": "tag-dark",
    "Health": "tag-pink",
    "Productivity": "tag-blue",
    "Social": "tag-mint",
    "Creator": "tag-yellow",
    "Creator Economy": "tag-yellow",
}


def _avatar_class_for_user(user) -> str:
    color = user.avatar_color if user and user.avatar_color else 1
    return f"avatar-{color}"


def _relative_time(dt) -> str:
    if not dt:
        return "just now"
    delta = datetime.utcnow() - dt
    if delta.days >= 30:
        months = max(1, delta.days // 30)
        return f"{months} month{'s' if months != 1 else ''} ago"
    if delta.days >= 7:
        weeks = max(1, delta.days // 7)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    if delta.days >= 1:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"
    return "just now"


def _serialize_explore_idea(idea: Idea) -> dict:
    author = idea.author
    stage_class = idea.stage or "validation"
    return {
        "id": idea.id,
        "title": idea.title,
        "summary": idea.summary,
        "category": idea.category,
        "tag_class": CATEGORY_TAG_CLASS.get(idea.category, "tag-brand"),
        "stage_class": stage_class,
        "stage": stage_class.capitalize(),
        "author": {
            "name": author.display_name if author else "Unknown user",
            "initials": author.initials if author else "NA",
            "avatar_class": _avatar_class_for_user(author) if author else "avatar-1",
        },
        "posted": _relative_time(idea.created_at),
        "votes": idea.vote_count,
        "comments_total": idea.comment_count,
        "collaborators_total": idea.collaborator_count,
    }


def _serialize_detail_idea(idea: Idea) -> dict:
    author = idea.author
    stage_class = idea.stage or "validation"

    comments = (
        Comment.query.filter_by(idea_id=idea.id)
        .order_by(Comment.created_at.desc())
        .limit(10)
        .all()
    )
    comment_preview = [
        {
            "name": item.author.display_name if item.author else "Unknown user",
            "initials": item.author.initials if item.author else "NA",
            "avatar_class": _avatar_class_for_user(item.author) if item.author else "avatar-1",
            "time": _relative_time(item.created_at),
            "text": item.body,
            "likes": item.like_count or 0,
        }
        for item in comments
    ]

    collaborators = (
        Collaboration.query.filter_by(idea_id=idea.id, status="accepted")
        .order_by(Collaboration.joined_at.asc())
        .all()
    )
    collaborator_data = [
        {
            "name": entry.user.display_name if entry.user else "Unknown user",
            "initials": entry.user.initials if entry.user else "NA",
            "avatar_class": _avatar_class_for_user(entry.user) if entry.user else "avatar-1",
            "role": entry.role or "Contributor",
        }
        for entry in collaborators
    ]

    tags = [f"#{tag.name}" for tag in idea.tags]

    # Keep template contract stable: map DB fields to existing sections.
    sections = {
        "idea": idea.summary,
        "problem": idea.description,
        "solution_intro": "Initial version based on current idea description and metrics.",
        "solution_points": [],
    }

    return {
        "id": idea.id,
        "title": idea.title,
        "category": idea.category,
        "tag_class": CATEGORY_TAG_CLASS.get(idea.category, "tag-brand"),
        "stage_class": stage_class,
        "stage": stage_class.capitalize(),
        "author": {
            "name": author.display_name if author else "Unknown user",
            "initials": author.initials if author else "NA",
            "avatar_class": _avatar_class_for_user(author) if author else "avatar-1",
        },
        "posted": _relative_time(idea.created_at),
        "views": f"{idea.views:,} views",
        "votes": idea.vote_count,
        "comments_total": idea.comment_count,
        "collaborators_total": idea.collaborator_count,
        "sections": sections,
        "score": idea.overall_score,
        "score_breakdown": {
            "market": idea.market_score or 0,
            "support": idea.community_score or 0,
            "feasibility": idea.feasibility_score or 0,
            "differentiation": idea.differentiation_score or 0,
        },
        "tags": tags,
        "collaborators": collaborator_data,
        "discussion_preview": comment_preview,
    }


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
    query = Idea.query.filter_by(privacy="public")

    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "all").strip()
    stage = (request.args.get("stage") or "all").strip().lower()

    if q:
        like_expr = f"%{q}%"
        query = query.filter(
            (Idea.title.ilike(like_expr)) |
            (Idea.summary.ilike(like_expr)) |
            (Idea.category.ilike(like_expr))
        )

    if category and category.lower() != "all":
        query = query.filter(Idea.category == category)

    if stage and stage != "all":
        query = query.filter(Idea.stage == stage)

    ideas = query.order_by(Idea.created_at.desc()).all()
    return render_template(
        "explore.html",
        ideas=[_serialize_explore_idea(idea) for idea in ideas],
    )


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/ideas/<int:idea_id>")
def idea_detail(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    return render_template("idea_detail.html", idea=_serialize_detail_idea(idea))


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