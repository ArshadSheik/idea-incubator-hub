"""
tests/test_models.py  —  8 focused unit tests for core model behaviour.

Run with:  python -m pytest tests/test_models.py -v
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app import create_app
from models.models import db, User, Idea, Vote, Comment, Bookmark


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


def _user(app, username="testuser", email="test@example.com"):
    with app.app_context():
        u = User(first_name="Test", last_name="User",
                 username=username, email=email)
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()
        return u.id


def _idea(app, user_id):
    with app.app_context():
        idea = Idea(user_id=user_id, title="Test Idea",
                    summary="A summary.", description="Full desc.",
                    category="FinTech", stage="ideation", privacy="public")
        db.session.add(idea)
        db.session.commit()
        return idea.id


# ── 1. Password is never stored as plain text ──────────────────────

class TestUserAuth:

    def test_password_hashed_not_plaintext(self, app):
        uid = _user(app)
        with app.app_context():
            u = db.session.get(User, uid)
            assert u.password_hash != "password123"
            assert "pbkdf2" in u.password_hash or "scrypt" in u.password_hash

    def test_correct_password_accepted(self, app):
        uid = _user(app)
        with app.app_context():
            u = db.session.get(User, uid)
            assert u.check_password("password123") is True

    def test_wrong_password_rejected(self, app):
        uid = _user(app)
        with app.app_context():
            u = db.session.get(User, uid)
            assert u.check_password("wrong") is False


# ── 2. Computed display properties ────────────────────────────────

class TestUserProperties:

    def test_display_name_and_initials(self, app):
        with app.app_context():
            u = User(first_name="Arshad", last_name="Sheik",
                     username="arshad", email="arshad@example.com")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
            assert u.display_name == "Arshad Sheik"
            assert u.initials == "AS"


# ── 3. Idea counters update correctly ─────────────────────────────

class TestIdeaCounts:

    def test_vote_and_comment_counts(self, app):
        uid = _user(app)
        iid = _idea(app, uid)
        with app.app_context():
            idea = db.session.get(Idea, iid)
            assert idea.vote_count == 0 and idea.comment_count == 0
            db.session.add(Vote(user_id=uid, idea_id=iid))
            db.session.add(Comment(user_id=uid, idea_id=iid, body="Nice!"))
            db.session.commit()
            idea = db.session.get(Idea, iid)
            assert idea.vote_count == 1
            assert idea.comment_count == 1

    def test_has_voted_tracking(self, app):
        uid = _user(app)
        iid = _idea(app, uid)
        with app.app_context():
            u = db.session.get(User, uid)
            idea = db.session.get(Idea, iid)
            assert u.has_voted(idea) is False
            db.session.add(Vote(user_id=uid, idea_id=iid))
            db.session.commit()
            u = db.session.get(User, uid)
            idea = db.session.get(Idea, iid)
            assert u.has_voted(idea) is True


# ── 4. Database unique constraints ────────────────────────────────

class TestUniqueConstraints:

    def test_duplicate_vote_raises_integrity_error(self, app):
        uid = _user(app)
        iid = _idea(app, uid)
        with app.app_context():
            db.session.add(Vote(user_id=uid, idea_id=iid))
            db.session.commit()
            db.session.add(Vote(user_id=uid, idea_id=iid))
            with pytest.raises(IntegrityError):
                db.session.commit()

    def test_duplicate_email_raises_integrity_error(self, app):
        _user(app, username="user1", email="same@example.com")
        with app.app_context():
            u2 = User(first_name="A", last_name="B",
                      username="user2", email="same@example.com")
            u2.set_password("password123")
            db.session.add(u2)
            with pytest.raises(IntegrityError):
                db.session.commit()
