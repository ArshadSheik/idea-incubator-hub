"""
tests/test_models.py

Unit tests for all database models and their computed properties.
Uses TestingConfig (in-memory SQLite, CSRF disabled) so tests are
fully isolated from the dev database and from each other.

Run with:
    python -m pytest tests/test_models.py -v
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from models.models import (
    db, User, Idea, Vote, Comment, Collaboration,
    Task, Bookmark, Notification
)


# ─────────────────────────────────────────────────────────────────
# FIXTURES — shared setup used by multiple tests
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def app():
    """Create a fresh Flask app with in-memory DB for each test function."""
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    """Flask test client."""
    return app.test_client()


def _make_user(app, first="Test", last="User",
               username="testuser", email="test@example.com",
               password="password123"):
    """Helper — creates and commits a user, returns the User object."""
    with app.app_context():
        user = User(
            first_name=first, last_name=last,
            username=username, email=email,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id  # return id so tests can re-query inside app context


def _make_idea(app, user_id, title="Test Idea",
               summary="A test summary.", category="FinTech",
               stage="ideation", privacy="public"):
    """Helper — creates and commits an idea, returns the Idea id."""
    with app.app_context():
        idea = Idea(
            user_id=user_id, title=title, summary=summary,
            description="Full description here.",
            category=category, stage=stage, privacy=privacy,
        )
        db.session.add(idea)
        db.session.commit()
        return idea.id


# ─────────────────────────────────────────────────────────────────
# USER MODEL TESTS
# ─────────────────────────────────────────────────────────────────

class TestUserPassword:
    """Password is hashed with a salt — never stored as plain text."""

    def test_password_is_hashed(self, app):
        uid = _make_user(app)
        with app.app_context():
            user = User.query.get(uid)
            assert user.password_hash != "password123"
            assert user.password_hash is not None

    def test_correct_password_accepted(self, app):
        uid = _make_user(app)
        with app.app_context():
            user = User.query.get(uid)
            assert user.check_password("password123") is True

    def test_wrong_password_rejected(self, app):
        uid = _make_user(app)
        with app.app_context():
            user = User.query.get(uid)
            assert user.check_password("wrongpassword") is False

    def test_empty_password_rejected(self, app):
        uid = _make_user(app)
        with app.app_context():
            user = User.query.get(uid)
            assert user.check_password("") is False

    def test_hash_uses_pbkdf2(self, app):
        """Confirm Werkzeug uses pbkdf2 (salted hash) not plain MD5/SHA."""
        uid = _make_user(app)
        with app.app_context():
            user = User.query.get(uid)
            assert "pbkdf2" in user.password_hash or "scrypt" in user.password_hash


class TestUserProperties:
    """display_name, initials, idea_count computed properties."""

    def test_display_name(self, app):
        uid = _make_user(app, first="Arshad", last="Sheik")
        with app.app_context():
            user = User.query.get(uid)
            assert user.display_name == "Arshad Sheik"

    def test_initials(self, app):
        uid = _make_user(app, first="Arshad", last="Sheik")
        with app.app_context():
            user = User.query.get(uid)
            assert user.initials == "AS"

    def test_initials_uppercase(self, app):
        uid = _make_user(app, first="john", last="doe")
        with app.app_context():
            user = User.query.get(uid)
            assert user.initials == "JD"

    def test_idea_count_zero_initially(self, app):
        uid = _make_user(app)
        with app.app_context():
            user = User.query.get(uid)
            assert user.idea_count == 0

    def test_idea_count_increments(self, app):
        uid = _make_user(app)
        _make_idea(app, uid)
        _make_idea(app, uid, title="Second idea")
        with app.app_context():
            user = User.query.get(uid)
            assert user.idea_count == 2

    def test_has_voted_false_initially(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            user = User.query.get(uid)
            idea = Idea.query.get(iid)
            assert user.has_voted(idea) is False

    def test_has_voted_true_after_voting(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            db.session.add(Vote(user_id=uid, idea_id=iid))
            db.session.commit()
            user = User.query.get(uid)
            idea = Idea.query.get(iid)
            assert user.has_voted(idea) is True

    def test_is_collaborating_false_initially(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            user = User.query.get(uid)
            idea = Idea.query.get(iid)
            assert user.is_collaborating(idea) is False


# ─────────────────────────────────────────────────────────────────
# IDEA MODEL TESTS
# ─────────────────────────────────────────────────────────────────

class TestIdeaCounts:
    """vote_count, comment_count, collaborator_count computed properties."""

    def test_vote_count_zero_initially(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            idea = Idea.query.get(iid)
            assert idea.vote_count == 0

    def test_vote_count_increments(self, app):
        uid = _make_user(app)
        uid2 = _make_user(app, username="user2", email="u2@example.com")
        iid = _make_idea(app, uid)
        with app.app_context():
            db.session.add(Vote(user_id=uid2, idea_id=iid))
            db.session.commit()
            idea = Idea.query.get(iid)
            assert idea.vote_count == 1

    def test_comment_count_zero_initially(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            idea = Idea.query.get(iid)
            assert idea.comment_count == 0

    def test_comment_count_increments(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            db.session.add(Comment(user_id=uid, idea_id=iid, body="Great idea!"))
            db.session.commit()
            idea = Idea.query.get(iid)
            assert idea.comment_count == 1

    def test_collaborator_count_zero_initially(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            idea = Idea.query.get(iid)
            assert idea.collaborator_count == 0

    def test_collaborator_count_increments(self, app):
        uid = _make_user(app)
        uid2 = _make_user(app, username="collab", email="collab@example.com")
        iid = _make_idea(app, uid)
        with app.app_context():
            db.session.add(Collaboration(
                user_id=uid2, idea_id=iid,
                role="contributor", status="accepted"
            ))
            db.session.commit()
            idea = Idea.query.get(iid)
            assert idea.collaborator_count == 1


class TestIdeaScore:
    """overall_score is a weighted average of four dimension scores."""

    def test_overall_score_returns_integer(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            idea = Idea.query.get(iid)
            assert isinstance(idea.overall_score, (int, float))

    def test_overall_score_between_0_and_100(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            idea = Idea.query.get(iid)
            assert 0 <= idea.overall_score <= 100


class TestIdeaIncrementViews:
    """increment_views() increases the view counter and persists it."""

    def test_views_zero_initially(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            idea = Idea.query.get(iid)
            assert idea.views == 0

    def test_increment_views_increases_count(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            idea = Idea.query.get(iid)
            idea.increment_views()
            idea = Idea.query.get(iid)
            assert idea.views == 1

    def test_increment_views_multiple_times(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            for _ in range(5):
                idea = Idea.query.get(iid)
                idea.increment_views()
            idea = Idea.query.get(iid)
            assert idea.views == 5


# ─────────────────────────────────────────────────────────────────
# UNIQUE CONSTRAINT TESTS
# ─────────────────────────────────────────────────────────────────

class TestUniqueConstraints:
    """DB enforces one vote and one bookmark per user per idea."""

    def test_duplicate_vote_raises_integrity_error(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            db.session.add(Vote(user_id=uid, idea_id=iid))
            db.session.commit()
            db.session.add(Vote(user_id=uid, idea_id=iid))
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_duplicate_bookmark_raises_integrity_error(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            db.session.add(Bookmark(user_id=uid, idea_id=iid))
            db.session.commit()
            db.session.add(Bookmark(user_id=uid, idea_id=iid))
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_duplicate_username_raises_integrity_error(self, app):
        _make_user(app, username="samename")
        with app.app_context():
            user2 = User(
                first_name="Other", last_name="User",
                username="samename", email="other@example.com",
            )
            user2.set_password("password123")
            db.session.add(user2)
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_duplicate_email_raises_integrity_error(self, app):
        _make_user(app, email="same@example.com")
        with app.app_context():
            user2 = User(
                first_name="Other", last_name="User",
                username="otheruser", email="same@example.com",
            )
            user2.set_password("password123")
            db.session.add(user2)
            with pytest.raises(IntegrityError):
                db.session.commit()


# ─────────────────────────────────────────────────────────────────
# NOTIFICATION MODEL TESTS
# ─────────────────────────────────────────────────────────────────

class TestNotification:
    """Notifications are created and linked to users correctly."""

    def test_notification_created_and_linked(self, app):
        uid = _make_user(app)
        with app.app_context():
            notif = Notification(
                user_id=uid,
                type="vote",
                message="Someone upvoted your idea",
                link="/ideas/1",
            )
            db.session.add(notif)
            db.session.commit()
            saved = Notification.query.filter_by(user_id=uid).first()
            assert saved is not None
            assert saved.type == "vote"
            assert saved.is_read is False

    def test_notification_is_read_defaults_false(self, app):
        uid = _make_user(app)
        with app.app_context():
            notif = Notification(
                user_id=uid, type="comment",
                message="New comment", link="/ideas/1"
            )
            db.session.add(notif)
            db.session.commit()
            assert notif.is_read is False

    def test_notification_mark_as_read(self, app):
        uid = _make_user(app)
        with app.app_context():
            notif = Notification(
                user_id=uid, type="vote",
                message="Upvoted", link="/ideas/1"
            )
            db.session.add(notif)
            db.session.commit()
            notif.is_read = True
            db.session.commit()
            saved = Notification.query.get(notif.id)
            assert saved.is_read is True


# ─────────────────────────────────────────────────────────────────
# TASK MODEL TESTS
# ─────────────────────────────────────────────────────────────────

class TestTask:
    """Tasks are created with correct defaults and linked to ideas."""

    def test_task_created_with_todo_status(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            task = Task(
                idea_id=iid, created_by=uid,
                title="Build MVP", status="todo", priority="medium"
            )
            db.session.add(task)
            db.session.commit()
            saved = Task.query.filter_by(idea_id=iid).first()
            assert saved.status == "todo"
            assert saved.priority == "medium"

    def test_task_status_can_be_updated(self, app):
        uid = _make_user(app)
        iid = _make_idea(app, uid)
        with app.app_context():
            task = Task(
                idea_id=iid, created_by=uid,
                title="Design mockup", status="todo", priority="high"
            )
            db.session.add(task)
            db.session.commit()
            task.status = "done"
            db.session.commit()
            saved = Task.query.get(task.id)
            assert saved.status == "done"