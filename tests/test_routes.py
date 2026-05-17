"""
tests/test_routes.py  —  17 focused integration tests covering the full
request-response cycle across 7 functional areas.

Run with:  python -m pytest tests/test_routes.py -v
"""

import json
import pytest

from app import create_app
from models.models import db, User, Idea, UserFollow
from routes.auth import generate_reset_token


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def app():
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def auth_client(app):
    """Test client logged in as testuser."""
    with app.app_context():
        u = User(first_name="Test", last_name="User",
                 username="testuser", email="test@example.com")
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()
    c = app.test_client()
    c.post("/auth/login",
           data={"email": "test@example.com", "password": "password123"},
           follow_redirects=True)
    return c


@pytest.fixture(scope="function")
def sample_idea(app):
    """Public idea owned by a different user (not testuser)."""
    with app.app_context():
        owner = User(first_name="Owner", last_name="User",
                     username="ideaowner", email="owner@example.com")
        owner.set_password("password123")
        db.session.add(owner)
        db.session.commit()
        idea = Idea(user_id=owner.id, title="Sample Idea",
                    summary="A summary.", description="Full desc.",
                    category="FinTech", stage="ideation", privacy="public")
        db.session.add(idea)
        db.session.commit()
        return idea.id


# ── 1. Public pages load without login ────────────────────────────

class TestPublicPages:

    def test_home_and_explore_accessible(self, client):
        assert client.get("/").status_code == 200
        assert client.get("/explore").status_code == 200

    def test_unknown_route_returns_404(self, client):
        assert client.get("/this-does-not-exist").status_code == 404


# ── 2. Registration ───────────────────────────────────────────────

class TestRegistration:

    def test_register_creates_user_and_redirects_to_dashboard(self, client, app):
        r = client.post("/auth/register", data={
            "first_name": "New", "last_name": "User",
            "username": "newuser", "email": "new@example.com",
            "password": "password123", "confirm_password": "password123",
        }, follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "dashboard" in r.headers.get("Location", "")
        with app.app_context():
            assert User.query.filter_by(email="new@example.com").first() is not None

    def test_duplicate_email_rejected(self, client, app):
        with app.app_context():
            u = User(first_name="Existing", last_name="User",
                     username="existing", email="exists@example.com")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
        r = client.post("/auth/register", data={
            "first_name": "New", "last_name": "User",
            "username": "newuser2", "email": "exists@example.com",
            "password": "password123", "confirm_password": "password123",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b"already exists" in r.data or b"email" in r.data.lower()


# ── 3. Login / Logout ─────────────────────────────────────────────

class TestLogin:

    def _create_user(self, app):
        with app.app_context():
            u = User(first_name="L", last_name="T",
                     username="logintest", email="login@example.com")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()

    def test_login_valid_credentials_redirects_to_dashboard(self, client, app):
        self._create_user(app)
        r = client.post("/auth/login",
                        data={"email": "login@example.com", "password": "password123"},
                        follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "dashboard" in r.headers.get("Location", "")

    def test_wrong_password_shows_error(self, client, app):
        self._create_user(app)
        r = client.post("/auth/login",
                        data={"email": "login@example.com", "password": "wrong"},
                        follow_redirects=True)
        assert r.status_code == 200
        assert b"Incorrect" in r.data or b"incorrect" in r.data

    def test_logout_redirects(self, client, app):
        self._create_user(app)
        client.post("/auth/login",
                    data={"email": "login@example.com", "password": "password123"},
                    follow_redirects=True)
        r = client.get("/auth/logout", follow_redirects=False)
        assert r.status_code in (301, 302)


# ── 4. Access control ─────────────────────────────────────────────

class TestAccessControl:

    def test_protected_pages_redirect_guests_to_login(self, client):
        for url in ["/dashboard", "/ideas/new"]:
            r = client.get(url, follow_redirects=False)
            assert r.status_code in (301, 302), f"{url} should redirect"
            assert "login" in r.headers.get("Location", "").lower()

    def test_dashboard_accessible_when_logged_in(self, auth_client):
        assert auth_client.get("/dashboard").status_code == 200

    def test_private_idea_returns_403_for_non_owner(self, app, auth_client):
        with app.app_context():
            other = User(first_name="O", last_name="U",
                         username="otheruser", email="other@example.com")
            other.set_password("password123")
            db.session.add(other)
            db.session.commit()
            idea = Idea(user_id=other.id, title="Private",
                        summary="s.", description="d.",
                        category="FinTech", stage="ideation", privacy="private")
            db.session.add(idea)
            db.session.commit()
            idea_id = idea.id
        assert auth_client.get(f"/ideas/{idea_id}").status_code == 403


# ── 5. Idea submit and view ───────────────────────────────────────

class TestIdeaFlow:

    def test_submit_idea_saves_to_db_and_redirects(self, auth_client, app):
        r = auth_client.post("/ideas/new", data={
            "title": "My Startup Idea",
            "summary": "A compelling one-line summary of the idea.",
            "description": "Full description of the idea goes here.",
            "category": "FinTech", "stage": "ideation",
            "privacy": "public", "emoji": "💡", "tags": "ai, startup",
        }, follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "/ideas/" in r.headers.get("Location", "")
        with app.app_context():
            assert Idea.query.filter_by(title="My Startup Idea").first() is not None

    def test_public_idea_viewable_by_anonymous_user(self, client, sample_idea):
        r = client.get(f"/ideas/{sample_idea}")
        assert r.status_code == 200, "Public ideas must be viewable without login"


# ── 6. Vote, comment, bookmark, collaborate ───────────────────────

class TestSocialInteractions:

    def test_vote_toggle_on_and_off(self, auth_client, sample_idea):
        r1 = auth_client.post(f"/ideas/{sample_idea}/vote",
                               content_type="application/json")
        d1 = json.loads(r1.data)
        assert d1["ok"] is True and d1["voted"] is True and d1["vote_count"] == 1

        r2 = auth_client.post(f"/ideas/{sample_idea}/vote",
                               content_type="application/json")
        d2 = json.loads(r2.data)
        assert d2["voted"] is False and d2["vote_count"] == 0

    def test_vote_requires_login(self, client, sample_idea):
        r = client.post(f"/ideas/{sample_idea}/vote",
                        content_type="application/json",
                        follow_redirects=False)
        assert r.status_code in (302, 401)

    def test_comment_created_and_empty_body_rejected(self, auth_client, sample_idea):
        r = auth_client.post(f"/ideas/{sample_idea}/comments",
                             json={"text": "Great idea!"})
        assert r.status_code == 201
        assert json.loads(r.data)["ok"] is True

        r2 = auth_client.post(f"/ideas/{sample_idea}/comments",
                              json={"text": ""})
        assert r2.status_code == 400

    def test_bookmark_toggles_on_and_off(self, auth_client, sample_idea):
        r1 = auth_client.post(f"/api/ideas/{sample_idea}/bookmark",
                               content_type="application/json")
        assert json.loads(r1.data)["bookmarked"] is True

        r2 = auth_client.post(f"/api/ideas/{sample_idea}/bookmark",
                               content_type="application/json")
        assert json.loads(r2.data)["bookmarked"] is False

    def test_collaborate_toggles_on_and_off(self, auth_client, sample_idea):
        r1 = auth_client.post(f"/ideas/{sample_idea}/collaborate",
                               content_type="application/json")
        assert json.loads(r1.data)["collaborating"] is True

        r2 = auth_client.post(f"/ideas/{sample_idea}/collaborate",
                               content_type="application/json")
        assert json.loads(r2.data)["collaborating"] is False


# ── 7. Password reset flow ────────────────────────────────────────

class TestPasswordReset:

    def test_full_reset_flow(self, client, app):
        with app.app_context():
            u = User(first_name="R", last_name="U",
                     username="resetuser", email="reset@example.com")
            u.set_password("oldpassword1")
            db.session.add(u)
            db.session.commit()
            token = generate_reset_token("reset@example.com")

        # Valid token shows reset form
        assert client.get(f"/auth/reset-password/{token}").status_code == 200

        # Invalid token redirects to forgot-password
        r = client.get("/auth/reset-password/badtoken", follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "forgot" in r.headers.get("Location", "").lower()

        # Successful password update redirects to login
        r2 = client.post(f"/auth/reset-password/{token}",
                         data={"password": "newpassword1",
                               "confirm_password": "newpassword1"},
                         follow_redirects=False)
        assert r2.status_code in (301, 302)
        assert "login" in r2.headers.get("Location", "").lower()

        with app.app_context():
            u = User.query.filter_by(email="reset@example.com").first()
            assert u.check_password("newpassword1")
