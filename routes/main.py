import json
import os
import uuid
from urllib import error as urlerror
from urllib import request as urlrequest
from datetime import datetime, timedelta

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from werkzeug.utils import secure_filename
from flask import current_app

from models.models import (
    AIAnalysis,
    Bookmark,
    Collaboration,
    Comment,
    Idea,
    IdeaMedia,
    Notification,
    Tag,
    Task,
    User,
    UserFollow,
    Vote,
    db,
    idea_tags,
)

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

STAGE_FLOW = ["ideation", "validation", "building", "launched"]
COLLABORATOR_ROLE_SUGGESTIONS = {
    "FinTech": ["Backend developer", "Compliance advisor", "Product designer"],
    "EdTech": ["Learning designer", "Frontend developer", "Growth marketer"],
    "GreenTech": ["Operations specialist", "Data analyst", "Partnership lead"],
    "DevTools": ["Developer advocate", "Backend developer", "Product manager"],
    "Health": ["Domain expert", "Backend developer", "UX researcher"],
    "Productivity": ["Frontend developer", "Product designer", "Growth marketer"],
    "Social": ["Community manager", "Frontend developer", "Growth marketer"],
    "Creator": ["Creator partnerships", "Product designer", "Growth marketer"],
    "Creator Economy": ["Creator partnerships", "Product manager", "Growth marketer"],
}


def _avatar_class_for_user(user) -> str:
    color = user.avatar_color if user and user.avatar_color else 1
    return f"avatar-{color}"


def _relative_time(dt) -> str:
    if not dt:
        return "just now"

    delta = datetime.utcnow() - dt
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        minutes = max(1, seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    if seconds < 86400:
        hours = max(1, seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    if delta.days >= 30:
        months = max(1, delta.days // 30)
        return f"{months} month{'s' if months != 1 else ''} ago"
    if delta.days >= 7:
        weeks = max(1, delta.days // 7)
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"


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
            "username": author.username if author else None,
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
        "views": f"{(idea.views or 0):,}",
        "updated": f"Updated {_relative_time(idea.updated_at or idea.created_at)}",
    }


def _serialize_public_snapshot_idea(idea: Idea) -> dict:
    stage_class = idea.stage or "validation"
    return {
        "id": idea.id,
        "title": idea.title,
        "category": idea.category,
        "tag_class": CATEGORY_TAG_CLASS.get(idea.category, "tag-brand"),
        "summary": idea.summary,
        "stage": stage_class.capitalize(),
        "stage_class": stage_class,
        "votes": idea.vote_count,
        "comments": idea.comment_count,
    }


def _build_public_market_trends() -> list[dict]:
    categories = (
        db.session.query(Idea.category, func.count(Idea.id).label("idea_count"))
        .filter_by(privacy="public")
        .group_by(Idea.category)
        .order_by(func.count(Idea.id).desc())
        .limit(4)
        .all()
    )
    total_public_ideas = Idea.query.filter_by(privacy="public").count() or 1
    trend_items = []
    for category, count in categories:
        percentage = int((count / total_public_ideas) * 100)
        trend_items.append(
            {
                "category": category,
                "idea_count": count,
                "share_percent": percentage,
            }
        )
    return trend_items


def _build_public_explore_context() -> dict:
    snapshot_ideas = (
        Idea.query.filter_by(privacy="public")
        .order_by(Idea.created_at.desc())
        .limit(8)
        .all()
    )
    return {
        "market_trends": _build_public_market_trends(),
        "idea_snapshot": [_serialize_public_snapshot_idea(idea) for idea in snapshot_ideas],
        "total_public_ideas": Idea.query.filter_by(privacy="public").count(),
        "total_builders": User.query.count(),
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

def _build_dashboard_tip(ideas, stats):
    if not ideas:
        return {
            "icon": "bi bi-stars",
            "title": "Start your first idea",
            "body": "You have not posted any ideas yet. Start by sharing one idea and collecting early feedback.",
            "action_label": "Post a new idea",
            "action_url": url_for("main.submit_idea"),
        }

    top_idea = max(
        ideas,
        key=lambda idea: (idea.vote_count or 0) + (idea.comment_count or 0) + (idea.collaborator_count or 0),
    )

    if stats["comments_received"] > 0:
        return {
            "icon": "bi bi-chat-heart",
            "title": "Review your feedback",
            "body": f'Your idea "{top_idea.title}" is getting community feedback. Check the comments and refine your pitch.',
            "action_label": "Open top idea",
            "action_url": url_for("main.idea_detail", idea_id=top_idea.id),
        }

    if stats["upvotes_received"] > 0:
        return {
            "icon": "bi bi-graph-up-arrow",
            "title": "Build on your traction",
            "body": f'Your idea "{top_idea.title}" has early votes. Add more detail or invite collaborators to keep momentum.',
            "action_label": "View idea",
            "action_url": url_for("main.idea_detail", idea_id=top_idea.id),
        }

    return {
        "icon": "bi bi-megaphone",
        "title": "Get your first signal",
        "body": "Your ideas are live, but they need more community signals. Share them and ask for feedback.",
        "action_label": "Browse community",
        "action_url": url_for("main.explore"),
    }

def _serialize_detail_idea(idea: Idea) -> dict:
    author = idea.author
    stage_class = idea.stage or "validation"
    actor = current_user if current_user and current_user.is_authenticated else None
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
    can_follow_author = (
        actor is not None and author is not None and actor.id != author.id
    )
    user_follows_author = (
        actor.follows(author) if can_follow_author else False
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
    collaborator_needs = _suggest_collaborator_needs(idea, collaborator_data)
    related_ideas = (
        Idea.query.filter(
            Idea.privacy == "public",
            Idea.id != idea.id,
            Idea.category == idea.category,
        )
        .order_by(Idea.created_at.desc())
        .limit(3)
        .all()
    )
    if not related_ideas:
        related_ideas = (
            Idea.query.filter(
                Idea.privacy == "public",
                Idea.id != idea.id,
            )
            .order_by(Idea.created_at.desc())
            .limit(3)
            .all()
        )

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
            "username": author.username if author else None,
            "initials": author.initials if author else "NA",
            "avatar_class": _avatar_class_for_user(author) if author else "avatar-1",
        },
        "can_follow_author": can_follow_author,
        "user_follows_author": user_follows_author,
        "emoji": idea.emoji or "💡",
        "posted": _relative_time(idea.created_at),
        "views": f"{idea.views:,} views",
        "votes": idea.vote_count,
        "user_voted": user_voted,
        "user_collaborating": user_collaborating,
        "is_owner": actor is not None and actor.id == idea.user_id,
        "comments_total": idea.comment_count,
        "collaborators_total": idea.collaborator_count,
        "stage_timeline": _build_stage_timeline(stage_class),
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
        "collaborator_needs": collaborator_needs,
        "related_ideas": [_serialize_related_idea(item) for item in related_ideas],
        "weekly_momentum": _build_weekly_momentum(idea.id),
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


def _build_stage_timeline(current_stage: str | None) -> list[dict]:
    stage = (current_stage or "validation").lower()
    current_idx = STAGE_FLOW.index(stage) if stage in STAGE_FLOW else 1
    timeline = []
    for idx, key in enumerate(STAGE_FLOW):
        if idx < current_idx:
            state = "completed"
        elif idx == current_idx:
            state = "active"
        else:
            state = "upcoming"
        timeline.append(
            {
                "key": key,
                "label": key.capitalize(),
                "state": state,
            }
        )
    return timeline


def _suggest_collaborator_needs(idea: Idea, collaborators: list[dict]) -> list[str]:
    suggestions = COLLABORATOR_ROLE_SUGGESTIONS.get(
        idea.category,
        ["Backend developer", "Product designer", "Growth marketer"],
    )
    existing_roles = {str(item.get("role", "")).strip().lower() for item in collaborators}
    needed = []
    for role in suggestions:
        role_lower = role.lower()
        if all(role_lower not in existing for existing in existing_roles):
            needed.append(role)
    return needed[:3]


def _serialize_related_idea(idea: Idea) -> dict:
    return {
        "id": idea.id,
        "title": idea.title,
        "category": idea.category,
        "tag_class": CATEGORY_TAG_CLASS.get(idea.category, "tag-brand"),
        "summary": idea.summary,
        "votes": idea.vote_count,
    }


def _build_weekly_momentum(idea_id: int) -> dict:
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=6)

    vote_rows = (
        db.session.query(Vote.created_at)
        .filter(
            Vote.idea_id == idea_id,
            Vote.created_at >= datetime.combine(start_date, datetime.min.time()),
        )
        .all()
    )
    comment_rows = (
        db.session.query(Comment.created_at)
        .filter(
            Comment.idea_id == idea_id,
            Comment.created_at >= datetime.combine(start_date, datetime.min.time()),
        )
        .all()
    )

    vote_by_day: dict[str, int] = {}
    comment_by_day: dict[str, int] = {}
    for (dt,) in vote_rows:
        key = dt.date().isoformat()
        vote_by_day[key] = vote_by_day.get(key, 0) + 1
    for (dt,) in comment_rows:
        key = dt.date().isoformat()
        comment_by_day[key] = comment_by_day.get(key, 0) + 1

    points = []
    max_total = 1
    for day_offset in range(7):
        day = start_date + timedelta(days=day_offset)
        key = day.isoformat()
        votes = vote_by_day.get(key, 0)
        comments = comment_by_day.get(key, 0)
        total = votes + comments
        max_total = max(max_total, total)
        points.append(
            {
                "label": day.strftime("%a"),
                "votes": votes,
                "comments": comments,
                "total": total,
            }
        )
    return {"points": points, "max_total": max_total}


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
    tag_filter = (request.args.get("tag")      or "").strip().lower()

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

    if tag_filter:
        query = (
            query
            .join(idea_tags, Idea.id == idea_tags.c.idea_id)
            .join(Tag, Tag.id == idea_tags.c.tag_id)
            .filter(func.lower(Tag.name) == tag_filter)
        )

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
            "tag": tag_filter or "",
        },
    )


@main_bp.route("/explore/public")
def explore_public():
    return redirect(url_for("main.explore"))


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
    dashboard_tip = _build_dashboard_tip(ideas, stats)

    weekly_digest = (
        Idea.query
        .filter_by(privacy="public")
        .outerjoin(Vote, Vote.idea_id == Idea.id)
        .group_by(Idea.id)
        .order_by(func.count(Vote.id).desc(), Idea.created_at.desc())
        .limit(3)
        .all()
    )

    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    suggested_users = (
        User.query
        .filter(User.id != current_user.id)
        .order_by(func.random())
        .limit(4)
        .all()
    )

    return render_template(
        "dashboard.html",
        stats=stats,
        stage_counts=stage_counts,
        my_ideas=[_serialize_dashboard_idea(idea) for idea in ideas],
        recent_activity=recent_activity,
        dashboard_tip=dashboard_tip,
        weekly_digest=weekly_digest,
        greeting=greeting,
        suggested_users=suggested_users
    )


@main_bp.route("/ideas/<int:idea_id>")
@login_required
def idea_detail(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    idea.increment_views()
    return render_template("idea_detail.html", idea=_serialize_detail_idea(idea), idea_media=idea.media.all())


@main_bp.route("/ideas/<int:idea_id>/vote", methods=["POST"])
@login_required
def toggle_idea_vote(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    actor = current_user

    existing_vote = Vote.query.filter_by(user_id=actor.id, idea_id=idea.id).first()
    if existing_vote:
        db.session.delete(existing_vote)
        voted = False
    else:
        db.session.add(Vote(user_id=actor.id, idea_id=idea.id))
        voted = True

    db.session.commit()

    # Notify idea author if someone else voted
    if voted and idea.user_id != current_user.id:
        db.session.add(Notification(
            user_id=idea.user_id,
            type="vote",
            message=f"{current_user.display_name} upvoted your idea '{idea.title}'",
            link=f"/ideas/{idea.id}",
        ))
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
@login_required
def toggle_idea_collaboration(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    actor = current_user

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

    # Return updated collaborator list so JS can re-render without a refresh
    collaborators = (
        Collaboration.query
        .filter_by(idea_id=idea.id, status="accepted")
        .join(User, Collaboration.user_id == User.id)
        .all()
    )
    collab_data = [
        {
            "name": c.user.display_name,
            "initials": c.user.initials,
            "avatar_class": f"avatar-{c.user.avatar_color}",
            "role": c.role,
        }
        for c in collaborators
    ]

    return jsonify(
        {
            "ok": True,
            "idea_id": idea.id,
            "user_id": actor.id,
            "collaborating": collaborating,
            "collaborators_total": idea.collaborator_count,
            "collaborators": collab_data,
        }
    )


@main_bp.route("/ideas/<int:idea_id>/comments", methods=["POST"])
@login_required
def create_idea_comment(idea_id: int):
    idea = Idea.query.get_or_404(idea_id)
    actor = current_user

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

    # Notify idea author if someone else commented
    if comment.user_id != idea.user_id:
        db.session.add(Notification(
            user_id=idea.user_id,
            type="comment",
            message=f"{current_user.display_name} commented on your idea '{idea.title}'",
            link=f"/ideas/{idea.id}",
        ))
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
@login_required
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
@login_required
def create_comment_reply(idea_id: int, comment_id: int):
    idea = Idea.query.get_or_404(idea_id)
    parent_comment = Comment.query.filter_by(id=comment_id, idea_id=idea.id).first_or_404()
    actor = current_user

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


@main_bp.route("/ideas/<int:idea_id>/delete", methods=["POST"])
@login_required
def delete_idea(idea_id: int):
    """Delete an idea owned by the current user."""
    idea = Idea.query.get_or_404(idea_id)
    if idea.user_id != current_user.id:
        abort(403)

    # Keep deletes robust even when FK cascades are not configured on every table.
    Bookmark.query.filter_by(idea_id=idea.id).delete(synchronize_session=False)
    AIAnalysis.query.filter_by(idea_id=idea.id).delete(synchronize_session=False)
    Notification.query.filter_by(link=f"/ideas/{idea.id}").delete(synchronize_session=False)
    db.session.delete(idea)
    db.session.commit()
    flash("Idea deleted successfully.", "success")
    return redirect(url_for("main.profile", username=current_user.username))


@main_bp.route("/ideas/<int:idea_id>/ai-insights", methods=["POST"])
@login_required
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


@main_bp.route("/ideas/<int:idea_id>/stage", methods=["POST"])
@login_required
def update_idea_stage(idea_id: int):
    """Update idea stage. Only the idea owner can do this."""
    idea = Idea.query.get_or_404(idea_id)
    if idea.user_id != current_user.id:
        abort(403)

    payload = request.get_json(silent=True) or {}
    stage = (payload.get("stage") or request.form.get("stage") or "").strip().lower()
    if stage not in Idea.STAGES:
        return jsonify({"ok": False, "error": "Invalid stage value"}), 400

    idea.stage = stage
    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "idea_id": idea.id,
            "stage": stage.capitalize(),
            "stage_class": stage,
            "stage_timeline": _build_stage_timeline(stage),
        }
    )


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


@main_bp.route("/profile/<username>")
@login_required
def profile(username):
    profile_user = User.query.filter_by(username=username).first_or_404()

    ideas = (
        Idea.query
        .filter_by(user_id=profile_user.id, privacy='public')
        .order_by(Idea.created_at.desc())
        .all()
    )
    collaborations = (
        Collaboration.query
        .filter_by(user_id=profile_user.id, status='accepted')
        .all()
    )
    collab_count         = len(collaborations)
    total_votes_received = sum(i.vote_count for i in ideas)
    bookmark_count       = Bookmark.query.filter_by(user_id=profile_user.id).count()

    # Check if the logged-in user is viewing their own profile
    is_own_profile = (
        current_user.is_authenticated and current_user.id == profile_user.id
    )
    viewer_follows_profile = (
        not is_own_profile and current_user.follows(profile_user)
    )

    return render_template(
        "profile.html",
        profile_user=profile_user,
        ideas=ideas,
        collaborations=collaborations,
        collab_count=collab_count,
        bookmark_count=bookmark_count,
        total_votes_received=total_votes_received,
        is_own_profile=is_own_profile,
        viewer_follows_profile=viewer_follows_profile,
    )


@main_bp.route("/profile/<username>/follow", methods=["POST"])
@login_required
def profile_toggle_follow(username):
    """Create or delete a follow edge (current user ↔ profile user)."""
    target = User.query.filter_by(username=username).first_or_404()
    next_url = (request.form.get("next") or request.args.get("next") or "").strip()
    if not next_url.startswith("/"):
        next_url = url_for("main.profile", username=username)

    if target.id == current_user.id:
        return redirect(next_url)

    row = UserFollow.query.filter_by(
        follower_id=current_user.id, followed_id=target.id
    ).first()
    if row:
        db.session.delete(row)
    else:
        db.session.add(
            UserFollow(follower_id=current_user.id, followed_id=target.id)
        )
    db.session.commit()
    return redirect(next_url)

@main_bp.route("/about")
def about():
    about_stats = {
        "ideas": Idea.query.filter_by(privacy="public").count(),
        "users": User.query.count(),
        "votes": Vote.query.count(),
        "comments": Comment.query.count(),
        "collaborations": Collaboration.query.filter_by(status="accepted").count(),
    }
    team_members = [
        {"name": "Arshad Sheik",  "role": "Main Page & Architecture", "initials": "AS", "color": 1},
        {"name": "Dong Bo", "role": "Auth & Login",             "initials": "DB", "color": 2},
        {"name": "Cong Yuan", "role": "Explore Page",             "initials": "CY", "color": 3},
        {"name": "Yitian Kong", "role": "Dashboard",                "initials": "YK", "color": 4},
        {"name": "Members", "role": "Collaboration Board",      "initials": "MS", "color": 5},
    ]
    return render_template(
        "about.html",
        about_stats=about_stats,
        team_members=team_members,
    )


@main_bp.route("/api/stats")
def platform_stats():
    """Returns live platform counts — used by the About page stat counter animation."""
    return jsonify({
        "ideas":    Idea.query.filter_by(privacy='public').count(),
        "users":    User.query.count(),
        "votes":    Vote.query.count(),
        "comments": Comment.query.count(),
    })

@main_bp.route("/api/notifications")
@login_required
def get_notifications():
    """Returns the current user's 10 most recent notifications."""
    notifs = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )
    unread_count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()

    return jsonify({
        "ok": True,
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "message": n.message,
                "link": n.link,
                "is_read": n.is_read,
                "created_at": _relative_time(n.created_at),
            }
            for n in notifs
        ]
    })


@main_bp.route("/api/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notif_id: int):
    """Marks a single notification as read."""
    notif = Notification.query.filter_by(
        id=notif_id, user_id=current_user.id
    ).first_or_404()
    notif.is_read = True
    db.session.commit()
    return jsonify({"ok": True})


@main_bp.route("/api/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    """Marks all of the current user's notifications as read."""
    Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).update({"is_read": True})
    db.session.commit()
    return jsonify({"ok": True})

@main_bp.route("/api/profile/bookmarks")
@login_required
def profile_bookmarks():
    """Returns the current user's bookmarked ideas as serialized idea cards."""
    bookmarks = (
        Bookmark.query
        .filter_by(user_id=current_user.id)
        .order_by(Bookmark.created_at.desc())
        .all()
    )
    ideas = [b.idea for b in bookmarks if b.idea and b.idea.privacy == 'public']
    return jsonify({
        "ok": True,
        "bookmarks": [_serialize_explore_idea(idea) for idea in ideas]
    })

def _serialize_follow_user(user: User) -> dict:
    return {
        "username": user.username,
        "display_name": user.display_name,
        "initials": user.initials,
        "avatar_color": user.avatar_color,
    }

@main_bp.route("/api/profile/<username>/followers")
@login_required
def profile_followers(username):
    profile_user = User.query.filter_by(username=username).first_or_404()
    rows = (
        UserFollow.query
        .filter_by(followed_id=profile_user.id)
        .order_by(UserFollow.created_at.desc())
        .limit(50)
        .all()
    )
    users = [r.follower for r in rows if r.follower]
    return jsonify({"ok": True, "users": [_serialize_follow_user(u) for u in users]})

@main_bp.route("/api/profile/<username>/following")
@login_required
def profile_following(username):
    profile_user = User.query.filter_by(username=username).first_or_404()
    rows = (
        UserFollow.query
        .filter_by(follower_id=profile_user.id)
        .order_by(UserFollow.created_at.desc())
        .limit(50)
        .all()
    )
    users = [r.followed for r in rows if r.followed]
    return jsonify({"ok": True, "users": [_serialize_follow_user(u) for u in users]})


@main_bp.route("/api/ideas/<int:idea_id>/bookmark", methods=["POST"])
@login_required
def toggle_bookmark(idea_id: int):
    """Toggle a bookmark on an idea for the current user."""
    idea = Idea.query.get_or_404(idea_id)
    existing = Bookmark.query.filter_by(
        user_id=current_user.id, idea_id=idea.id
    ).first()

    if existing:
        db.session.delete(existing)
        bookmarked = False
    else:
        db.session.add(Bookmark(user_id=current_user.id, idea_id=idea.id))
        bookmarked = True

    db.session.commit()
    return jsonify({"ok": True, "bookmarked": bookmarked})


@main_bp.route("/api/ideas/<int:idea_id>/bookmark-status", methods=["GET"])
@login_required
def bookmark_status(idea_id: int):
    """Return bookmark state on an idea for the current user."""
    Idea.query.get_or_404(idea_id)
    existing = Bookmark.query.filter_by(
        user_id=current_user.id,
        idea_id=idea_id,
    ).first()
    return jsonify({"ok": True, "bookmarked": existing is not None})

@main_bp.route("/ideas/<int:idea_id>/board")
@login_required
def collaboration_board(idea_id: int):
    """Kanban board for an idea's collaboration team."""
    idea = Idea.query.get_or_404(idea_id)
    tasks = Task.query.filter_by(idea_id=idea_id).order_by(Task.created_at.asc()).all()
    team = (
        Collaboration.query
        .filter_by(idea_id=idea_id, status='accepted')
        .all()
    )
    team_members = [c.user for c in team if c.user]

    return render_template(
        "collaboration.html",
        idea=idea,
        tasks=tasks,
        team=team_members,
    )

def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in IdeaMedia.ALLOWED_EXTENSIONS


@main_bp.route("/ideas/<int:idea_id>/media", methods=["POST"])
@login_required
def upload_idea_media(idea_id: int):
    """AJAX: upload a file attachment to an idea. Author only."""
    idea = Idea.query.get_or_404(idea_id)

    if idea.user_id != current_user.id:
        return jsonify({"ok": False, "error": "Only the idea author can upload files."}), 403

    if idea.media.count() >= IdeaMedia.MAX_PER_IDEA:
        return jsonify({"ok": False, "error": f"Maximum {IdeaMedia.MAX_PER_IDEA} files per idea."}), 400

    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"ok": False, "error": "No file selected."}), 400

    if not _allowed_file(file.filename):
        return jsonify({"ok": False, "error": "File type not allowed. Accepted: jpg, png, gif, webp, pdf, pptx, docx."}), 400

    file_data = file.read()
    if len(file_data) > IdeaMedia.MAX_FILE_SIZE:
        return jsonify({"ok": False, "error": "File too large. Maximum 8 MB per file."}), 400

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit('.', 1)[-1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"

    idea_upload_dir = os.path.join(
        current_app.static_folder, 'uploads', 'ideas', str(idea_id)
    )
    os.makedirs(idea_upload_dir, exist_ok=True)
    with open(os.path.join(idea_upload_dir, stored_name), 'wb') as f:
        f.write(file_data)

    media = IdeaMedia(
        idea_id=idea.id,
        uploader_id=current_user.id,
        original_filename=original_name,
        stored_filename=stored_name,
        mime_type=file.mimetype or 'application/octet-stream',
        file_size=len(file_data),
    )
    db.session.add(media)
    db.session.commit()

    return jsonify({
        "ok": True,
        "media_id": media.id,
        "original_filename": media.original_filename,
        "is_image": media.is_image,
        "human_size": media.human_size,
        "url": url_for('static', filename=f'uploads/ideas/{idea_id}/{stored_name}'),
    })


@main_bp.route("/ideas/<int:idea_id>/media/<int:media_id>", methods=["DELETE"])
@login_required
def delete_idea_media(idea_id: int, media_id: int):
    """AJAX: delete an attachment. Author only."""
    media = IdeaMedia.query.filter_by(id=media_id, idea_id=idea_id).first_or_404()

    if Idea.query.get_or_404(idea_id).user_id != current_user.id:
        return jsonify({"ok": False, "error": "Permission denied."}), 403

    file_path = os.path.join(
        current_app.static_folder, 'uploads', 'ideas', str(idea_id), media.stored_filename
    )
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(media)
    db.session.commit()
    return jsonify({"ok": True, "media_id": media_id})

@main_bp.route("/api/ideas/<int:idea_id>/tasks", methods=["POST"])
@login_required
def create_task(idea_id: int):
    """Create a new task on the Kanban board."""
    Idea.query.get_or_404(idea_id)
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    if not title:
        return jsonify({"ok": False, "error": "Title is required"}), 400

    task = Task(
        idea_id=idea_id,
        created_by=current_user.id,
        assigned_to=payload.get("assigned_to") or None,
        title=title,
        description=payload.get("description", ""),
        status=payload.get("status", "todo"),
        priority=payload.get("priority", "medium"),
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"ok": True, "task_id": task.id}), 201


@main_bp.route("/api/ideas/<int:idea_id>/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task(idea_id: int, task_id: int):
    """Update a task — used for drag-and-drop status changes and edits."""
    task = Task.query.filter_by(id=task_id, idea_id=idea_id).first_or_404()
    payload = request.get_json(silent=True) or {}

    if "status" in payload:
        task.status = payload["status"]
    if "title" in payload:
        task.title = payload["title"]
    if "description" in payload:
        task.description = payload["description"]
    if "priority" in payload:
        task.priority = payload["priority"]
    if "assigned_to" in payload:
        task.assigned_to = payload["assigned_to"] or None

    db.session.commit()
    return jsonify({"ok": True})


@main_bp.route("/api/ideas/<int:idea_id>/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(idea_id: int, task_id: int):
    """Delete a task from the board."""
    task = Task.query.filter_by(id=task_id, idea_id=idea_id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({"ok": True})

@main_bp.route("/ideas/new", methods=["GET", "POST"])
@login_required
def submit_idea():
    from forms import IdeaForm
    form = IdeaForm()

    if form.validate_on_submit():
        # Parse tags from comma-separated string
        tag_names = [t.strip() for t in (form.tags.data or "").split(",") if t.strip()]
        tags = []
        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)
            tags.append(tag)

        idea = Idea(
            user_id     = current_user.id,
            title       = form.title.data,
            summary     = form.summary.data,
            description = form.description.data,
            category    = form.category.data,
            stage       = form.stage.data,
            privacy     = form.privacy.data,
            emoji       = form.emoji.data or "💡",
        )
        idea.tags = tags
        db.session.add(idea)
        db.session.commit()

        # Create a notification for the user confirming submission
        db.session.add(Notification(
            user_id = current_user.id,
            type    = "milestone",
            message = f"Your idea '{idea.title}' was posted successfully!",
            link    = f"/ideas/{idea.id}",
        ))
        db.session.commit()

        return redirect(url_for("main.idea_detail", idea_id=idea.id))

    return render_template("submit_idea.html", form=form)

@main_bp.route("/api/ideas/<int:idea_id>/news")
def idea_news(idea_id: int):
    """Market news for an idea's category — cached 24h."""
    idea = Idea.query.get_or_404(idea_id)
    try:
        from services.news_service import get_news_for_category
        articles = get_news_for_category(idea.category)
        return jsonify({"ok": True, "articles": articles})
    except Exception as e:
        return jsonify({"ok": False, "articles": [], "error": str(e)})


@main_bp.route("/api/trending-categories")
def trending_categories():
    """Returns category counts for the trending widget on explore."""
    from sqlalchemy import func
    rows = (
        db.session.query(Idea.category, func.count(Idea.id).label("count"))
        .filter_by(privacy="public")
        .group_by(Idea.category)
        .order_by(func.count(Idea.id).desc())
        .limit(6)
        .all()
    )
    return jsonify([{"category": r.category, "count": r.count} for r in rows])

@main_bp.route("/api/chart-data")
def chart_data():
    """Aggregated data for dashboard and explore charts."""
    from sqlalchemy import func

    # Ideas by stage
    stage_rows = (
        db.session.query(Idea.stage, func.count(Idea.id))
        .filter_by(privacy="public")
        .group_by(Idea.stage)
        .all()
    )

    # Ideas by category
    cat_rows = (
        db.session.query(Idea.category, func.count(Idea.id))
        .filter_by(privacy="public")
        .group_by(Idea.category)
        .order_by(func.count(Idea.id).desc())
        .limit(8)
        .all()
    )

    # Ideas submitted per day for last 7 days
    from datetime import datetime, timedelta
    seven_days = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().date() - timedelta(days=i)
        count = Idea.query.filter(
            db.func.date(Idea.created_at) == day,
            Idea.privacy == "public"
        ).count()
        seven_days.append({"date": day.strftime("%a"), "count": count})

    return jsonify({
        "by_stage":    [{"stage": r[0] or "ideation", "count": r[1]} for r in stage_rows],
        "by_category": [{"category": r[0], "count": r[1]} for r in cat_rows],
        "weekly":      seven_days,
    })

@main_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    from forms import ProfileEditForm
    form = ProfileEditForm(obj=current_user)

    if form.validate_on_submit():
        current_user.first_name   = form.first_name.data.strip()
        current_user.last_name    = form.last_name.data.strip()
        current_user.bio          = form.bio.data.strip()
        current_user.avatar_color = int(form.avatar_color.data)
        db.session.commit()
        return redirect(url_for("main.profile", username=current_user.username))

    return render_template("edit_profile.html", form=form)

@main_bp.route("/api/trending-hashtags")
def trending_hashtags():
    from datetime import datetime, timedelta
    from sqlalchemy import func

    results = (
        db.session.query(
            Tag.name,
            func.count(idea_tags.c.idea_id).label('total')
        )
        .join(idea_tags, Tag.id == idea_tags.c.tag_id)
        .group_by(Tag.id)
        .order_by(func.count(idea_tags.c.idea_id).desc())
        .limit(15)
        .all()
    )

    week_ago = datetime.utcnow() - timedelta(days=7)
    recent = (
        db.session.query(
            Tag.name,
            func.count(idea_tags.c.idea_id).label('recent')
        )
        .join(idea_tags, Tag.id == idea_tags.c.tag_id)
        .join(Idea, Idea.id == idea_tags.c.idea_id)
        .filter(Idea.created_at >= week_ago)
        .group_by(Tag.id)
        .all()
    )
    recent_map = {r.name: r.recent for r in recent}

    data = [
        {
            'tag': row.name,
            'total': row.total,
            'recent': recent_map.get(row.name, 0),
        }
        for row in results
    ]
    return jsonify(data)

@main_bp.route("/api/chat", methods=["POST"])
def chat_api():
    """Floating chatbot endpoint. Calls DeepSeek API."""
    data         = request.get_json(silent=True) or {}
    messages     = data.get("messages", [])
    idea_context = data.get("context", {})

    idea_hint = ""
    if idea_context.get("idea_id"):
        idea = Idea.query.get(idea_context["idea_id"])
        if idea:
            idea_hint = (
                f"\n\nThe user is currently viewing the idea: '{idea.title}' "
                f"(category: {idea.category}, stage: {idea.stage}). "
                f"Use this context to give relevant advice when appropriate."
            )

    user_context = ""
    if current_user.is_authenticated:
        user_context = f"\n\nThe user is logged in as {current_user.display_name}."
    else:
        user_context = "\n\nThe user is not logged in. If they ask about personal data, ideas, or profile — encourage them to sign up by clicking 'Get started' in the top navigation bar. Do not mention URL paths."
        
    system_prompt = (
        "You are the Idea Incubator Hub assistant. "
        "You help startup founders validate ideas and understand the platform. "
        "Keep responses concise (2-4 sentences) and actionable."
        + idea_hint + user_context
    )

    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        return jsonify({"reply": (
            "Hi! I'm the Idea Incubator assistant. I can help you validate startup ideas, "
            "understand platform features, and improve your pitches."
        )})

    try:
        import urllib.request as _urlreq
        payload = json.dumps({
            "model": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            "max_tokens": 300,
            "messages": [
                {"role": "system", "content": system_prompt},
                *messages[-10:],
            ],
            "temperature": 0.5,
        }).encode()

        req = _urlreq.Request(
            os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions"),
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with _urlreq.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read())
        reply = body["choices"][0]["message"]["content"].strip()
        return jsonify({"reply": reply})

    except Exception as e:
        current_app.logger.error(f"Chat API error: {e}")
        return jsonify({"reply": "Sorry, I had trouble responding. Please try again."}), 500
    