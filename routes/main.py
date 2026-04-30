import json
import os
from urllib import error as urlerror
from urllib import request as urlrequest
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

def _serialize_dashboard_idea(idea: Idea) -> dict:
    stage_class = idea.stage or "ideation"
    return {
        "id": idea.id,
        "title": idea.title,
        "summary": idea.summary,
        "emoji": idea.emoji or "💡",
        "stage_class": stage_class,
        "stage": stage_class.capitalize(),
        "votes": idea.vote_count,
        "comments": idea.comment_count,
        "collaborators": idea.collaborator_count,
        "views": f"{idea.views:,}",
        "updated": f"Updated {_relative_time(idea.updated_at or idea.created_at)}",
    }


def _build_dashboard_activity(user_id: int, limit: int = 6) -> list[dict]:
    items = []

    vote_rows = (
        db.session.query(Vote, Idea, User)
        .join(Idea, Vote.idea_id == Idea.id)
        .join(User, Vote.user_id == User.id)
        .filter(Idea.user_id == user_id, User.id != user_id)
        .order_by(Vote.created_at.desc())
        .limit(limit)
        .all()
    )
    for vote, idea, actor in vote_rows:
        items.append(
            {
                "kind": "vote",
                "icon_class": "act-vote",
                "icon": "bi bi-caret-up-fill",
                "actor": actor.display_name,
                "idea_title": idea.title,
                "idea_url": url_for("main.idea_detail", idea_id=idea.id),
                "text": "upvoted",
                "extra": None,
                "time": _relative_time(vote.created_at),
                "_sort_time": vote.created_at,
            }
        )

    comment_rows = (
        db.session.query(Comment, Idea, User)
        .join(Idea, Comment.idea_id == Idea.id)
        .join(User, Comment.user_id == User.id)
        .filter(Idea.user_id == user_id, User.id != user_id)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .all()
    )
    for comment, idea, actor in comment_rows:
        excerpt = comment.body.strip()
        if len(excerpt) > 90:
            excerpt = excerpt[:87] + "..."
        items.append(
            {
                "kind": "comment",
                "icon_class": "act-comment",
                "icon": "bi bi-chat-dots-fill",
                "actor": actor.display_name,
                "idea_title": idea.title,
                "idea_url": url_for("main.idea_detail", idea_id=idea.id),
                "text": "commented on",
                "extra": f'"{excerpt}"',
                "time": _relative_time(comment.created_at),
                "_sort_time": comment.created_at,
            }
        )

    collab_rows = (
        db.session.query(Collaboration, Idea, User)
        .join(Idea, Collaboration.idea_id == Idea.id)
        .join(User, Collaboration.user_id == User.id)
        .filter(
            Idea.user_id == user_id,
            Collaboration.status == "accepted",
            User.id != user_id,
        )
        .order_by(Collaboration.joined_at.desc())
        .limit(limit)
        .all()
    )
    for collab, idea, actor in collab_rows:
        items.append(
            {
                "kind": "collaboration",
                "icon_class": "act-join",
                "icon": "bi bi-person-plus-fill",
                "actor": actor.display_name,
                "idea_title": idea.title,
                "idea_url": url_for("main.idea_detail", idea_id=idea.id),
                "text": "joined",
                "extra": f"as a {collab.role.capitalize()}",
                "time": _relative_time(collab.joined_at),
                "_sort_time": collab.joined_at,
            }
        )

    items.sort(key=lambda x: x["_sort_time"] or datetime.min, reverse=True)
    return items[:limit]

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


def _build_ai_insights(idea: Idea) -> dict:
    """
    Lightweight rule-based "AI" insights so we can demo integration
    without requiring third-party model credentials.
    """
    summary = (
        f"{idea.title} is a {idea.stage} stage idea in {idea.category} focused on "
        f"{(idea.summary or '').strip().rstrip('.')}. This concept currently has "
        f"{idea.vote_count} votes and {idea.comment_count} discussion comments."
    )

    strengths = []
    if idea.market_score >= 80:
        strengths.append("Strong market potential score suggests clear user demand.")
    if idea.community_score >= 80:
        strengths.append("High community support indicates positive early validation.")
    if idea.vote_count >= 5:
        strengths.append("User voting activity suggests meaningful audience interest.")
    if not strengths:
        strengths.append("Early traction exists and can improve with more validation interviews.")

    suggestions = []
    if idea.feasibility_score < 70:
        suggestions.append("Define a scoped MVP with explicit technical milestones.")
    if idea.differentiation_score < 70:
        suggestions.append("Clarify your unique advantage compared to direct alternatives.")
    if idea.comment_count < 3:
        suggestions.append("Collect more structured feedback from target users this week.")
    if not suggestions:
        suggestions.append("Prioritize one KPI for the next sprint (retention, conversion, or activation).")

    return {
        "summary": summary,
        "strengths": strengths[:3],
        "suggestions": suggestions[:3],
    }


def _generate_ai_insights_with_openai(idea: Idea) -> dict:
    provider = os.getenv("AI_PROVIDER", "deepseek").strip().lower()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        endpoint = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
        provider_name = "openai"
    else:
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            # Fallback to OpenAI if DeepSeek key is missing.
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            if not api_key:
                raise RuntimeError("Configure DEEPSEEK_API_KEY or OPENAI_API_KEY.")
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            endpoint = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
            provider_name = "openai"
        else:
            model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            endpoint = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
            provider_name = "deepseek"
    prompt = (
        "You are a startup idea coach. Return strict JSON with this schema: "
        '{"summary": "string", "strengths": ["string"], "suggestions": ["string"]}. '
        "Keep strengths and suggestions to 2-3 concise bullets each.\n\n"
        f"Idea title: {idea.title}\n"
        f"Category: {idea.category}\n"
        f"Stage: {idea.stage}\n"
        f"Summary: {idea.summary}\n"
        f"Description: {idea.description}\n"
        f"Votes: {idea.vote_count}\n"
        f"Comments: {idea.comment_count}\n"
        f"Scores => market:{idea.market_score}, support:{idea.community_score}, "
        f"feasibility:{idea.feasibility_score}, differentiation:{idea.differentiation_score}\n"
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are concise, practical, and return valid JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.4,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(
        endpoint,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urlrequest.urlopen(req, timeout=20) as resp:
            response_json = json.loads(resp.read().decode("utf-8"))
    except urlerror.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"{provider_name} request failed: {exc.code} {detail}") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"{provider_name} request failed: {exc}") from exc

    content = (
        response_json.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    if not content:
        raise RuntimeError(f"{provider_name} returned empty content.")

    # Some models may wrap JSON in markdown fences.
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].strip()

    try:
        parsed = json.loads(content)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"{provider_name} returned non-JSON content.") from exc

    summary = str(parsed.get("summary", "")).strip()
    strengths = parsed.get("strengths", [])
    suggestions = parsed.get("suggestions", [])
    if not isinstance(strengths, list):
        strengths = []
    if not isinstance(suggestions, list):
        suggestions = []

    if not summary:
        raise RuntimeError(f"{provider_name} response missing summary.")

    return {
        "summary": summary,
        "strengths": [str(item).strip() for item in strengths if str(item).strip()][:3],
        "suggestions": [str(item).strip() for item in suggestions if str(item).strip()][:3],
        "provider": provider_name,
        "model": model,
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
@login_required
def dashboard():
    ideas = (
        Idea.query
        .filter_by(user_id=current_user.id)
        .order_by(Idea.updated_at.desc(), Idea.created_at.desc())
        .all()
    )

    stats = {
        "ideas_posted": len(ideas),
        "upvotes_received": (
            db.session.query(func.count(Vote.id))
            .join(Idea, Vote.idea_id == Idea.id)
            .filter(Idea.user_id == current_user.id)
            .scalar()
            or 0
        ),
        "comments_received": (
            db.session.query(func.count(Comment.id))
            .join(Idea, Comment.idea_id == Idea.id)
            .filter(Idea.user_id == current_user.id)
            .scalar()
            or 0
        ),
        "active_collaborators": (
            db.session.query(func.count(Collaboration.id))
            .join(Idea, Collaboration.idea_id == Idea.id)
            .filter(
                Idea.user_id == current_user.id,
                Collaboration.status == "accepted",
                Collaboration.user_id != current_user.id,
            )
            .scalar()
            or 0
        ),
    }

    stage_counts = {
        "all": len(ideas),
        "ideation": sum(1 for idea in ideas if idea.stage == "ideation"),
        "validation": sum(1 for idea in ideas if idea.stage == "validation"),
        "building": sum(1 for idea in ideas if idea.stage == "building"),
        "launched": sum(1 for idea in ideas if idea.stage == "launched"),
    }

    recent_activity = _build_dashboard_activity(current_user.id, limit=6)

    weekly_digest = (
        Idea.query
        .filter_by(privacy="public")
        .outerjoin(Vote, Vote.idea_id == Idea.id)
        .group_by(Idea.id)
        .order_by(func.count(Vote.id).desc(), Idea.created_at.desc())
        .limit(3)
        .all()
    )

    return render_template(
        "dashboard.html",
        stats=stats,
        stage_counts=stage_counts,
        my_ideas=[_serialize_dashboard_idea(idea) for idea in ideas],
        recent_activity=recent_activity,
        weekly_digest=weekly_digest,
    )


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


@main_bp.route("/ideas/<int:idea_id>/ai-insights", methods=["POST"])
def generate_idea_insights(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    try:
        insights = _generate_ai_insights_with_openai(idea)
        return jsonify(
            {
                "ok": True,
                "idea_id": idea.id,
                "insights": insights,
                "provider": insights.get("provider", "unknown"),
                "model": insights.get("model"),
            }
        )
    except RuntimeError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 502


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