import json
from datetime import datetime

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func

from models.models import Collaboration, Comment, Idea, User, Vote, db

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


def _format_comment_time(dt) -> str:
    if not dt:
        return "Unknown time"
    return dt.strftime("%Y-%m-%d %H:%M")


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
    actor = _get_actor_user()
    user_voted = False
    user_collaborating = False
    if actor is not None:
        user_voted = (
            Vote.query.filter_by(user_id=actor.id, idea_id=idea.id).first() is not None
        )
        user_collaborating = (
            Collaboration.query.filter_by(
                user_id=actor.id,
                idea_id=idea.id,
                status="accepted",
            ).first()
            is not None
        )

    comments = (
        Comment.query.filter_by(idea_id=idea.id)
        .filter(Comment.parent_id.is_(None))
        .order_by(Comment.created_at.desc())
        .limit(10)
        .all()
    )
    comment_preview = [
        {
            "id": item.id,
            "name": item.author.display_name if item.author else "Unknown user",
            "initials": item.author.initials if item.author else "NA",
            "avatar_class": _avatar_class_for_user(item.author) if item.author else "avatar-1",
            "time": _format_comment_time(item.created_at),
            "text": item.body,
            "likes": item.like_count or 0,
            "replies": [
                _serialize_comment(reply)
                for reply in Comment.query.filter_by(parent_id=item.id)
                .order_by(Comment.created_at.asc())
                .all()
            ],
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

    description_text = idea.description or ""
    parsed_meta = {}
    if description_text.strip().startswith("{"):
        try:
            parsed_meta = json.loads(description_text)
        except (TypeError, ValueError):
            parsed_meta = {}

    sections_source = parsed_meta.get("sections", {}) if isinstance(parsed_meta, dict) else {}

    # Keep template contract stable: map DB fields to existing sections.
    sections = {
        "idea": sections_source.get("idea", idea.summary),
        "problem": sections_source.get("problem", description_text),
        "solution_intro": sections_source.get(
            "solution_intro",
            "Initial version based on current idea description and metrics.",
        ),
        "solution_points": sections_source.get("solution_points", []),
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
        "user_voted": user_voted,
        "user_collaborating": user_collaborating,
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


def _serialize_comment(comment: Comment) -> dict:
    author = comment.author
    return {
        "id": comment.id,
        "idea_id": comment.idea_id,
        "name": author.display_name if author else "Unknown user",
        "initials": author.initials if author else "NA",
        "avatar_class": _avatar_class_for_user(author) if author else "avatar-1",
        "time": _format_comment_time(comment.created_at),
        "text": comment.body,
        "likes": comment.like_count or 0,
        "parent_id": comment.parent_id,
    }


def _get_actor_user():
    """
    Temporary actor resolution for write endpoints:
    - use logged-in user when available
    - otherwise fallback to first seeded user for local development
    """
    if current_user and current_user.is_authenticated:
        return current_user
    return User.query.order_by(User.id.asc()).first()


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
    sort = (request.args.get("sort") or "trending").strip().lower()

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

    if sort == "newest":
        query = query.order_by(Idea.created_at.desc())
    elif sort == "votes":
        query = (
            query
            .outerjoin(Vote, Vote.idea_id == Idea.id)
            .group_by(Idea.id)
            .order_by(func.count(Vote.id).desc(), Idea.created_at.desc())
        )
    else:
        # Keep trending stable for now: latest public ideas first.
        query = query.order_by(Idea.created_at.desc())

    ideas = query.all()
    return render_template(
        "explore.html",
        ideas=[_serialize_explore_idea(idea) for idea in ideas],
        active_filters={
            "q": q,
            "category": category or "all",
            "stage": stage or "all",
            "sort": sort or "trending",
        },
    )


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/ideas/<int:idea_id>")
def idea_detail(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    return render_template("idea_detail.html", idea=_serialize_detail_idea(idea))


@main_bp.route("/ideas/<int:idea_id>/vote", methods=["POST"])
def toggle_idea_vote(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    actor = _get_actor_user()
    if actor is None:
        return jsonify({"ok": False, "error": "No available user to cast vote"}), 400

    existing_vote = Vote.query.filter_by(user_id=actor.id, idea_id=idea.id).first()
    if existing_vote:
        db.session.delete(existing_vote)
        voted = False
    else:
        db.session.add(Vote(user_id=actor.id, idea_id=idea.id))
        voted = True

    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "idea_id": idea.id,
            "user_id": actor.id,
            "voted": voted,
            "vote_count": idea.vote_count,
        }
    )


@main_bp.route("/ideas/<int:idea_id>/collaborate", methods=["POST"])
def toggle_idea_collaboration(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    actor = _get_actor_user()
    if actor is None:
        return jsonify({"ok": False, "error": "No available user to collaborate"}), 400

    existing = Collaboration.query.filter_by(
        user_id=actor.id,
        idea_id=idea.id,
        status="accepted",
    ).first()
    if existing:
        db.session.delete(existing)
        collaborating = False
    else:
        db.session.add(
            Collaboration(
                user_id=actor.id,
                idea_id=idea.id,
                role="contributor",
                status="accepted",
            )
        )
        collaborating = True

    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "idea_id": idea.id,
            "user_id": actor.id,
            "collaborating": collaborating,
            "collaborators_total": idea.collaborator_count,
        }
    )


@main_bp.route("/ideas/<int:idea_id>/comments", methods=["POST"])
def create_idea_comment(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    actor = _get_actor_user()
    if actor is None:
        return jsonify({"ok": False, "error": "No available user to post comment"}), 400

    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or request.form.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "Comment text is required"}), 400
    if len(text) > 1000:
        return jsonify({"ok": False, "error": "Comment must be 1000 characters or less"}), 400

    comment = Comment(
        user_id=actor.id,
        idea_id=idea.id,
        body=text,
    )
    db.session.add(comment)
    db.session.commit()

    return (
        jsonify(
            {
                "ok": True,
                "comment": _serialize_comment(comment),
                "comments_total": idea.comment_count,
            }
        ),
        201,
    )


@main_bp.route("/ideas/<int:idea_id>/comments/<int:comment_id>/like", methods=["POST"])
def toggle_comment_like(idea_id: int, comment_id: int):
    idea = Idea.query.get_or_404(idea_id)
    comment = Comment.query.filter_by(id=comment_id, idea_id=idea.id).first_or_404()

    payload = request.get_json(silent=True) or {}
    action = (payload.get("action") or "toggle").strip().lower()
    if action not in {"like", "unlike", "toggle"}:
        return jsonify({"ok": False, "error": "Invalid action"}), 400

    # For now we persist aggregate likes; per-user state is restored on frontend.
    if action == "like":
        comment.like_count = (comment.like_count or 0) + 1
        liked = True
    elif action == "unlike":
        comment.like_count = max((comment.like_count or 0) - 1, 0)
        liked = False
    else:
        currently_liked = bool(payload.get("currently_liked", False))
        if currently_liked:
            comment.like_count = max((comment.like_count or 0) - 1, 0)
            liked = False
        else:
            comment.like_count = (comment.like_count or 0) + 1
            liked = True

    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "idea_id": idea.id,
            "comment_id": comment.id,
            "liked": liked,
            "like_count": comment.like_count or 0,
        }
    )


@main_bp.route("/ideas/<int:idea_id>/comments/<int:comment_id>/replies", methods=["POST"])
def create_comment_reply(idea_id: int, comment_id: int):
    idea = Idea.query.get_or_404(idea_id)
    parent_comment = Comment.query.filter_by(id=comment_id, idea_id=idea.id).first_or_404()
    actor = _get_actor_user()
    if actor is None:
        return jsonify({"ok": False, "error": "No available user to post reply"}), 400

    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or request.form.get("text") or "").strip()
    if not text:
        return jsonify({"ok": False, "error": "Reply text is required"}), 400
    if len(text) > 1000:
        return jsonify({"ok": False, "error": "Reply must be 1000 characters or less"}), 400

    reply = Comment(
        user_id=actor.id,
        idea_id=idea.id,
        parent_id=parent_comment.id,
        body=text,
    )
    db.session.add(reply)
    db.session.commit()

    return jsonify({"ok": True, "reply": _serialize_comment(reply)}), 201


@main_bp.route("/login")
def login():
    return redirect(url_for("auth.login"))

@main_bp.route("/register")
def register():
    return redirect(url_for("auth.register"))


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
    return redirect(url_for("auth.login"))


@main_bp.route("/register.html")
def register_html():
    return redirect(url_for("auth.register"))