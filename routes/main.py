"""
routes/main.py  —  Routes for the main/public-facing pages.

This is YOUR blueprint as the main page developer.
Add new routes here as you wire up more of the frontend.
"""

from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import desc, func

from models.models import db, Idea, Vote, Tag, User

main_bp = Blueprint('main', __name__)


# ─────────────────────────────────────────
# HOME / INDEX  —  the main page you built
# ─────────────────────────────────────────
@main_bp.route('/')
@main_bp.route('/index')
def index():
    """
    Renders the main landing/home page.

    Passes to the template:
      - trending_ideas  : top 3 ideas by vote count (for the trending cards)
      - recent_ideas    : latest 6 public ideas (for the feed/explore section)
      - total_ideas     : site-wide count (for the stats bar)
      - total_users     : site-wide count
      - categories      : list of category strings for the filter buttons
    """
    # Top 3 ideas by vote count — used for the "Trending" cards
    trending_ideas = (
        db.session.query(Idea)
        .filter(Idea.privacy == 'public')
        .outerjoin(Vote)
        .group_by(Idea.id)
        .order_by(desc(func.count(Vote.id)))
        .limit(3)
        .all()
    )

    # 6 most recent public ideas — used for the main feed
    recent_ideas = (
        Idea.query
        .filter(Idea.privacy == 'public')
        .order_by(desc(Idea.created_at))
        .limit(6)
        .all()
    )

    # Site-wide stats for the stats bar
    total_ideas = Idea.query.filter_by(privacy='public').count()
    total_users = User.query.count()

    return render_template(
        'index.html',
        trending_ideas=trending_ideas,
        recent_ideas=recent_ideas,
        total_ideas=total_ideas,
        total_users=total_users,
        categories=Idea.CATEGORIES,
    )


# ─────────────────────────────────────────
# AJAX: VOTE ON AN IDEA
# ─────────────────────────────────────────
@main_bp.route('/ideas/<int:idea_id>/vote', methods=['POST'])
@login_required
def vote_idea(idea_id):
    """
    Toggle an upvote on an idea. Called via AJAX from the main page cards
    and the idea detail page.

    Returns JSON: { voted: bool, vote_count: int }
    """
    idea = Idea.query.get_or_404(idea_id)
    existing_vote = Vote.query.filter_by(
        user_id=current_user.id,
        idea_id=idea_id
    ).first()

    if existing_vote:
        # Already voted — remove the vote (toggle off)
        db.session.delete(existing_vote)
        db.session.commit()
        return jsonify({'voted': False, 'vote_count': idea.vote_count})
    else:
        # New vote
        vote = Vote(user_id=current_user.id, idea_id=idea_id)
        db.session.add(vote)
        db.session.commit()
        return jsonify({'voted': True, 'vote_count': idea.vote_count})


# ─────────────────────────────────────────
# AJAX: FILTER IDEAS BY CATEGORY
# ─────────────────────────────────────────
@main_bp.route('/ideas/filter')
def filter_ideas():
    """
    Returns filtered idea cards as JSON.
    Query params:
      ?category=FinTech   (omit for all categories)
      ?sort=recent|votes  (default: recent)
      ?page=1
    """
    category = request.args.get('category', '')
    sort     = request.args.get('sort', 'recent')
    page     = request.args.get('page', 1, type=int)

    query = Idea.query.filter(Idea.privacy == 'public')

    if category and category != 'all':
        query = query.filter(Idea.category == category)

    if sort == 'votes':
        query = query.outerjoin(Vote).group_by(Idea.id).order_by(desc(func.count(Vote.id)))
    else:
        query = query.order_by(desc(Idea.created_at))

    ideas = query.paginate(page=page, per_page=6, error_out=False)

    ideas_data = [{
        'id':            idea.id,
        'title':         idea.title,
        'summary':       idea.summary,
        'category':      idea.category,
        'stage':         idea.stage,
        'emoji':         idea.emoji,
        'vote_count':    idea.vote_count,
        'comment_count': idea.comment_count,
        'author':        idea.author.display_name,
        'created_at':    idea.created_at.strftime('%b %d, %Y'),
    } for idea in ideas.items]

    return jsonify({
        'ideas':    ideas_data,
        'has_next': ideas.has_next,
        'page':     ideas.page,
    })
