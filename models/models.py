"""
models.py
All SQLAlchemy database models for Idea Incubator Hub.

Tables:
  - User
  - UserFollow   (followers / following edges)
  - Idea
  - Vote          (users upvoting ideas)
  - Comment       (threaded comments on ideas)
  - Tag / IdeaTag (many-to-many tagging)
  - Collaboration (users joining idea teams)
  - Task          (kanban tasks on collaboration board)
  - Notification
  - Bookmark
  - AI Analysis
  - Market Trend (cached external API data)
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─────────────────────────────────────────
# Association table: ideas ↔ tags (many-to-many)
# ─────────────────────────────────────────
idea_tags = db.Table(
    'idea_tags',
    db.Column('idea_id', db.Integer, db.ForeignKey('ideas.id'), primary_key=True),
    db.Column('tag_id',  db.Integer, db.ForeignKey('tags.id'),  primary_key=True),
)


# ─────────────────────────────────────────
# USER
# ─────────────────────────────────────────
class User(UserMixin, db.Model):
    """
    Represents a registered user.
    UserMixin provides Flask-Login helpers: is_authenticated, is_active, get_id()
    """
    __tablename__ = 'users'

    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email        = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    # Profile fields
    first_name   = db.Column(db.String(50), nullable=False)
    last_name    = db.Column(db.String(50), nullable=False)
    bio          = db.Column(db.Text, default='')
    # avatar_color maps to CSS class .avatar-1 through .avatar-6
    avatar_color = db.Column(db.Integer, default=1)

    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Relationships ──────────────────────────────────────────────
    ideas          = db.relationship('Idea', backref='author', lazy='dynamic',
                                     foreign_keys='Idea.user_id')
    votes          = db.relationship('Vote', backref='voter', lazy='dynamic')
    comments       = db.relationship('Comment', backref='author', lazy='dynamic')
    collaborations = db.relationship('Collaboration', backref='user', lazy='dynamic')

    # ── Password helpers ───────────────────────────────────────────
    def set_password(self, password):
        """Hash and salt the password before storing — NEVER store plain text."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a plain-text password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    # ── Computed properties ────────────────────────────────────────
    @property
    def display_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def initials(self):
        return f'{self.first_name[0]}{self.last_name[0]}'.upper()

    @property
    def idea_count(self):
        return self.ideas.count()

    def has_voted(self, idea):
        """Check whether this user has already voted on a given idea."""
        return Vote.query.filter_by(user_id=self.id, idea_id=idea.id).first() is not None

    def is_collaborating(self, idea):
        """Check whether this user is an accepted collaborator on an idea."""
        return Collaboration.query.filter_by(
            user_id=self.id, idea_id=idea.id, status='accepted'
        ).first() is not None

    @property
    def followers_count(self) -> int:
        return UserFollow.query.filter_by(followed_id=self.id).count()

    @property
    def following_count(self) -> int:
        return UserFollow.query.filter_by(follower_id=self.id).count()

    def follows(self, other: 'User') -> bool:
        if other is None or other.id == self.id:
            return False
        return UserFollow.query.filter_by(
            follower_id=self.id, followed_id=other.id
        ).first() is not None

    def __repr__(self):
        return f'<User {self.username}>'


# ─────────────────────────────────────────
# USER FOLLOW (directed edge: follower → followed)
# ─────────────────────────────────────────
class UserFollow(db.Model):
    """
    A follows B: follower_id=A, followed_id=B.
    No self-follow (enforced in routes).
    """
    __tablename__ = 'user_follows'
    __table_args__ = (
        db.UniqueConstraint('follower_id', 'followed_id', name='uq_user_follow_pair'),
    )

    id          = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    follower = db.relationship(
        'User', foreign_keys=[follower_id], backref=db.backref('_out_follows', lazy='dynamic')
    )
    followed = db.relationship(
        'User', foreign_keys=[followed_id], backref=db.backref('_in_follows', lazy='dynamic')
    )

    def __repr__(self):
        return f'<UserFollow {self.follower_id} → {self.followed_id}>'


# ─────────────────────────────────────────
# IDEA
# ─────────────────────────────────────────
class Idea(db.Model):
    """
    A startup idea posted by a user.
    """
    __tablename__ = 'ideas'

    # Valid choices for category, stage, privacy
    CATEGORIES = [
        'FinTech', 'EdTech', 'GreenTech', 'Health',
        'DevTools', 'Productivity', 'Social', 'Creator Economy', 'Other'
    ]
    STAGES = ['ideation', 'validation', 'building', 'launched']
    PRIVACY = ['public', 'unlisted', 'private']

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title       = db.Column(db.String(80),  nullable=False)
    summary     = db.Column(db.String(200), nullable=False)   # short blurb on cards
    description = db.Column(db.Text,        nullable=False)   # full markdown body
    category    = db.Column(db.String(30),  nullable=False, default='Other')
    stage       = db.Column(db.String(20),  nullable=False, default='ideation')
    privacy     = db.Column(db.String(10),  nullable=False, default='public')
    emoji       = db.Column(db.String(10),  default='💡')

    # Analytics scores (0–100), calculated/updated server-side
    market_score          = db.Column(db.Integer, default=0)
    community_score       = db.Column(db.Integer, default=0)
    feasibility_score     = db.Column(db.Integer, default=0)
    differentiation_score = db.Column(db.Integer, default=0)

    views      = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ── Relationships ──────────────────────────────────────────────
    votes          = db.relationship('Vote',          backref='idea', lazy='dynamic',
                                     cascade='all, delete-orphan')
    comments       = db.relationship('Comment',       backref='idea', lazy='dynamic',
                                     cascade='all, delete-orphan')
    tags           = db.relationship('Tag', secondary=idea_tags, backref='ideas', lazy='subquery')
    collaborations = db.relationship('Collaboration', backref='idea', lazy='dynamic',
                                     cascade='all, delete-orphan')
    tasks          = db.relationship('Task',          backref='idea', lazy='dynamic',
                                     cascade='all, delete-orphan')

    # ── Computed properties ────────────────────────────────────────
    @property
    def vote_count(self):
        return self.votes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def collaborator_count(self):
        return self.collaborations.filter_by(status='accepted').count()

    @property
    def overall_score(self):
        """Weighted average of the four dimension scores."""
        scores = [
            self.market_score,
            self.community_score,
            self.feasibility_score,
            self.differentiation_score,
        ]
        filled = [s for s in scores if s > 0]
        return round(sum(filled) / len(filled)) if filled else 0

    @property
    def stage_percent(self):
        """Progress bar width for the stage indicator."""
        mapping = {'ideation': 10, 'validation': 35, 'building': 65, 'launched': 100}
        return mapping.get(self.stage, 0)

    def increment_views(self):
        """Call this whenever the idea detail page is loaded."""
        self.views += 1
        db.session.commit()

    def __repr__(self):
        return f'<Idea {self.id}: {self.title}>'


# ─────────────────────────────────────────
# VOTE
# ─────────────────────────────────────────
class Vote(db.Model):
    """
    A single upvote from one user on one idea.
    The unique constraint prevents duplicate voting.
    """
    __tablename__ = 'votes'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'idea_id', name='unique_vote'),
    )

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    idea_id    = db.Column(db.Integer, db.ForeignKey('ideas.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Vote user={self.user_id} idea={self.idea_id}>'


# ─────────────────────────────────────────
# COMMENT
# ─────────────────────────────────────────
class Comment(db.Model):
    """
    A comment on an idea, with optional threading via parent_id.
    """
    __tablename__ = 'comments'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    idea_id    = db.Column(db.Integer, db.ForeignKey('ideas.id'), nullable=False)
    # parent_id is NULL for top-level comments, set for replies
    parent_id  = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)

    body       = db.Column(db.Text, nullable=False)
    like_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Self-referential relationship for threaded replies
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                              lazy='dynamic')

    def __repr__(self):
        return f'<Comment {self.id} on idea={self.idea_id}>'


# ─────────────────────────────────────────
# TAG
# ─────────────────────────────────────────
class Tag(db.Model):
    """
    A keyword tag that can be applied to many ideas (many-to-many via idea_tags).
    """
    __tablename__ = 'tags'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'


# ─────────────────────────────────────────
# COLLABORATION
# ─────────────────────────────────────────
class Collaboration(db.Model):
    """
    Records a user joining (or requesting to join) an idea's team.
    status: 'pending' | 'accepted' | 'rejected'
    role:   'contributor' | 'reviewer' | 'lead'
    """
    __tablename__ = 'collaborations'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'idea_id', name='unique_collaboration'),
    )

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    idea_id    = db.Column(db.Integer, db.ForeignKey('ideas.id'), nullable=False)
    status     = db.Column(db.String(10), default='accepted')  # auto-accept for now
    role       = db.Column(db.String(20), default='contributor')
    joined_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Collaboration user={self.user_id} idea={self.idea_id} role={self.role}>'


# ─────────────────────────────────────────
# TASK  (Kanban board on collaboration page)
# ─────────────────────────────────────────
class Task(db.Model):
    """
    A kanban task attached to an idea's collaboration board.
    status: 'todo' | 'in_progress' | 'done'
    """
    __tablename__ = 'tasks'

    id          = db.Column(db.Integer, primary_key=True)
    idea_id     = db.Column(db.Integer, db.ForeignKey('ideas.id'), nullable=False)
    # The user who created the task
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # The user the task is assigned to (optional)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    title       = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='')
    status      = db.Column(db.String(20), default='todo')
    priority    = db.Column(db.String(10), default='medium')  # low | medium | high
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Explicit foreign_keys needed because Task references users.id twice
    creator  = db.relationship('User', foreign_keys=[created_by])
    assignee = db.relationship('User', foreign_keys=[assigned_to])

    def __repr__(self):
        return f'<Task {self.id}: {self.title} [{self.status}]>'

# ─────────────────────────────────────────
# IDEA MEDIA  (attached images / files)
# ─────────────────────────────────────────
class IdeaMedia(db.Model):
    """
    A file (image, PDF, etc.) attached to an idea.
    Stored in static/uploads/ideas/<idea_id>/ with a UUID-based filename.
    Max 3 files per idea, 8 MB per file.
    """
    __tablename__ = 'idea_media'

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'pptx', 'docx'}
    MAX_FILE_SIZE      = 8 * 1024 * 1024   # 8 MB
    MAX_PER_IDEA       = 3

    id                = db.Column(db.Integer, primary_key=True)
    idea_id           = db.Column(db.Integer, db.ForeignKey('ideas.id'), nullable=False)
    uploader_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename   = db.Column(db.String(255), nullable=False)
    mime_type         = db.Column(db.String(100), nullable=False)
    file_size         = db.Column(db.Integer, nullable=False)
    uploaded_at       = db.Column(db.DateTime, default=datetime.utcnow)

    idea     = db.relationship('Idea', backref=db.backref('media', lazy='dynamic',
                               cascade='all, delete-orphan'))
    uploader = db.relationship('User')

    @property
    def is_image(self):
        return self.mime_type.startswith('image/')

    @property
    def extension(self):
        return self.original_filename.rsplit('.', 1)[-1].lower() if '.' in self.original_filename else ''

    @property
    def human_size(self):
        size = self.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size // 1024} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def __repr__(self):
        return f'<IdeaMedia {self.id}: {self.original_filename} on idea={self.idea_id}>'

# ─────────────────────────────────────────
# NOTIFICATION
# ─────────────────────────────────────────
class Notification(db.Model):
    """
    In-app notification for a user.
    type examples: 'vote', 'comment', 'reply', 'collab_request', 'collab_accepted', 'milestone'
    """
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type       = db.Column(db.String(30), nullable=False)
    message    = db.Column(db.String(300), nullable=False)
    link       = db.Column(db.String(200), nullable=True)   # URL to navigate to on click
    is_read    = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f'<Notification {self.type} → user={self.user_id}>'


# ─────────────────────────────────────────
# BOOKMARK
# ─────────────────────────────────────────
class Bookmark(db.Model):
    """
    A user saving an idea to their bookmarks for later reference.
    Unique constraint prevents duplicate bookmarks.
    """
    __tablename__ = 'bookmarks'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'idea_id', name='unique_bookmark'),
    )

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    idea_id    = db.Column(db.Integer, db.ForeignKey('ideas.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('bookmarks', lazy='dynamic'))
    idea = db.relationship('Idea', backref=db.backref('bookmarks', lazy='dynamic'))

    def __repr__(self):
        return f'<Bookmark user={self.user_id} idea={self.idea_id}>'


# ─────────────────────────────────────────
# AI ANALYSIS
# ─────────────────────────────────────────
class AIAnalysis(db.Model):
    """
    Cached result of an AI analysis run on an idea.
    One row per idea — re-running overwrites the existing row.
    Storing results avoids repeated API calls for the same idea.
    """
    __tablename__ = 'ai_analyses'

    id                   = db.Column(db.Integer, primary_key=True)
    idea_id              = db.Column(db.Integer, db.ForeignKey('ideas.id'),
                                     nullable=False, unique=True)
    market_summary       = db.Column(db.Text, nullable=True)
    feasibility_summary  = db.Column(db.Text, nullable=True)
    competitor_summary   = db.Column(db.Text, nullable=True)
    strengths_json       = db.Column(db.Text, nullable=True)   # JSON list of strings
    risks_json           = db.Column(db.Text, nullable=True)   # JSON list of strings
    sentiment_score      = db.Column(db.Integer, nullable=True)  # 0–100
    created_at           = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at           = db.Column(db.DateTime, default=datetime.utcnow,
                                     onupdate=datetime.utcnow)

    idea = db.relationship('Idea', backref=db.backref('ai_analysis', uselist=False))

    def strengths(self):
        """Return strengths as a Python list."""
        import json
        return json.loads(self.strengths_json) if self.strengths_json else []

    def risks(self):
        """Return risks as a Python list."""
        import json
        return json.loads(self.risks_json) if self.risks_json else []

    def __repr__(self):
        return f'<AIAnalysis idea={self.idea_id} score={self.sentiment_score}>'


# ─────────────────────────────────────────
# MARKET TREND  (cached external API data)
# ─────────────────────────────────────────
class MarketTrend(db.Model):
    """
    Cached market/trend data fetched from external APIs (NewsAPI, Alpha Vantage, etc.)
    Keyed by category + source so we can cache per-category per-API.
    Stale after 24 hours — routes check fetched_at before deciding to refresh.
    """
    __tablename__ = 'market_trends'

    id          = db.Column(db.Integer, primary_key=True)
    category    = db.Column(db.String(30), nullable=False)   # e.g. 'FinTech'
    source      = db.Column(db.String(30), nullable=False)   # e.g. 'newsapi', 'alphavantage'
    data_json   = db.Column(db.Text, nullable=False)          # raw JSON string from API
    fetched_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def data(self):
        """Return the cached data as a Python dict/list."""
        import json
        return json.loads(self.data_json)

    def is_stale(self, max_age_hours=24):
        """Returns True if this cache entry is older than max_age_hours."""
        from datetime import timedelta
        return datetime.utcnow() - self.fetched_at > timedelta(hours=max_age_hours)

    def __repr__(self):
        return f'<MarketTrend {self.category}/{self.source} fetched={self.fetched_at}>'
    
# ─────────────────────────────────────────
# DIRECT MESSAGE  (user-to-user messages)
# ─────────────────────────────────────────
class DirectMessage(db.Model):
    __tablename__ = "direct_messages"

    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    sender = db.relationship("User", foreign_keys=[sender_id], lazy="joined")
    recipient = db.relationship("User", foreign_keys=[recipient_id], lazy="joined")

    def __repr__(self):
        return f"<DirectMessage {self.sender_id} -> {self.recipient_id}>"