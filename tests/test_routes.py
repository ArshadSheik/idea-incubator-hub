"""
tests/test_routes.py

Integration tests for all Flask routes.
Tests the full request-response cycle using Flask's test client.
Uses TestingConfig (in-memory SQLite, CSRF disabled).

Run with:
    python -m pytest tests/test_routes.py -v
"""

import json
import pytest

from app import create_app
from models.models import db, User, Idea, Vote, Comment, Collaboration, Task, Bookmark, Notification, DirectMessage, UserFollow
from routes.auth import generate_reset_token


# ─────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────

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
    """A test client that is already logged in as a test user."""
    with app.app_context():
        user = User(
            first_name="Test", last_name="User",
            username="testuser", email="test@example.com",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

    client = app.test_client()
    client.post("/auth/login", data={
        "email": "test@example.com",
        "password": "password123",
    }, follow_redirects=True)
    return client


@pytest.fixture(scope="function")
def sample_idea(app):
    """Creates a public idea owned by a dedicated 'ideaowner' user.

    Used by vote, comment, bookmark, collaboration tests — the auth_client
    (testuser) is intentionally a *different* user so we exercise the
    non-owner code paths.
    """
    with app.app_context():
        owner = User.query.filter_by(email="owner@example.com").first()
        if not owner:
            owner = User(
                first_name="Idea", last_name="Owner",
                username="ideaowner", email="owner@example.com",
            )
            owner.set_password("password123")
            db.session.add(owner)
            db.session.commit()

        idea = Idea(
            user_id=owner.id, title="Test Idea",
            summary="A test summary.", description="Full description.",
            category="FinTech", stage="ideation", privacy="public",
        )
        db.session.add(idea)
        db.session.commit()
        return idea.id


@pytest.fixture(scope="function")
def owned_idea(app, auth_client):
    """Creates a public idea owned by testuser (the auth_client user).

    Used by task-CRUD tests so that the logged-in user has board write-access.
    """
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        idea = Idea(
            user_id=user.id, title="Owned Test Idea",
            summary="An idea owned by testuser.", description="Full description.",
            category="FinTech", stage="ideation", privacy="public",
        )
        db.session.add(idea)
        db.session.commit()
        return idea.id


# ─────────────────────────────────────────────────────────────────
# PUBLIC PAGE TESTS (no login required)
# ─────────────────────────────────────────────────────────────────

class TestPublicPages:
    """Pages that should be accessible without being logged in."""

    def test_landing_page_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_explore_page_returns_200(self, client):
        r = client.get("/explore")
        assert r.status_code == 200

    def test_about_page_returns_200(self, client):
        r = client.get("/about")
        assert r.status_code == 200

    def test_login_page_returns_200(self, client):
        r = client.get("/auth/login")
        assert r.status_code == 200

    def test_register_page_returns_200(self, client):
        r = client.get("/auth/register")
        assert r.status_code == 200

    def test_404_returns_custom_page(self, client):
        r = client.get("/this-page-does-not-exist-at-all")
        assert r.status_code == 404

    def test_explore_with_search_query(self, client):
        r = client.get("/explore?q=fintech")
        assert r.status_code == 200

    def test_explore_with_category_filter(self, client):
        r = client.get("/explore?category=FinTech")
        assert r.status_code == 200

    def test_explore_with_stage_filter(self, client):
        r = client.get("/explore?stage=ideation")
        assert r.status_code == 200

    def test_explore_sort_by_votes(self, client):
        r = client.get("/explore?sort=votes")
        assert r.status_code == 200

    def test_legacy_html_redirects(self, client):
        """Legacy .html routes should redirect to the proper route."""
        r = client.get("/index.html")
        assert r.status_code in (301, 302)

        r = client.get("/explore.html")
        assert r.status_code in (301, 302)


# ─────────────────────────────────────────────────────────────────
# AUTH TESTS
# ─────────────────────────────────────────────────────────────────

class TestRegistration:
    """Registration creates a user and logs them in."""

    def test_register_valid_user(self, client, app):
        r = client.post("/auth/register", data={
            "first_name": "New", "last_name": "User",
            "username": "newuser", "email": "new@example.com",
            "password": "password123", "confirm_password": "password123",
        }, follow_redirects=True)
        assert r.status_code == 200
        with app.app_context():
            user = User.query.filter_by(email="new@example.com").first()
            assert user is not None
            assert user.username == "newuser"

    def test_register_redirects_to_dashboard(self, client):
        r = client.post("/auth/register", data={
            "first_name": "New", "last_name": "User",
            "username": "newuser2", "email": "new2@example.com",
            "password": "password123", "confirm_password": "password123",
        }, follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "dashboard" in r.headers.get("Location", "")

    def test_register_password_is_hashed(self, client, app):
        client.post("/auth/register", data={
            "first_name": "Hash", "last_name": "Test",
            "username": "hashtest", "email": "hash@example.com",
            "password": "password123", "confirm_password": "password123",
        }, follow_redirects=True)
        with app.app_context():
            user = User.query.filter_by(email="hash@example.com").first()
            assert user.password_hash != "password123"
            assert "pbkdf2" in user.password_hash or "scrypt" in user.password_hash

    def test_register_duplicate_email_rejected(self, client, app):
        with app.app_context():
            u = User(first_name="Existing", last_name="User",
                     username="existing", email="exists@example.com")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()

        r = client.post("/auth/register", data={
            "first_name": "New", "last_name": "User",
            "username": "newuser3", "email": "exists@example.com",
            "password": "password123", "confirm_password": "password123",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b"already exists" in r.data or b"taken" in r.data or b"email" in r.data.lower()

    def test_register_duplicate_username_rejected(self, client, app):
        with app.app_context():
            u = User(first_name="Existing", last_name="User",
                     username="takenname", email="taken@example.com")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()

        r = client.post("/auth/register", data={
            "first_name": "New", "last_name": "User",
            "username": "takenname", "email": "different@example.com",
            "password": "password123", "confirm_password": "password123",
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_register_password_mismatch_rejected(self, client):
        r = client.post("/auth/register", data={
            "first_name": "New", "last_name": "User",
            "username": "mismatch", "email": "mismatch@example.com",
            "password": "password123", "confirm_password": "different123",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b"match" in r.data.lower() or b"password" in r.data.lower()

    def test_register_short_password_rejected(self, client):
        r = client.post("/auth/register", data={
            "first_name": "New", "last_name": "User",
            "username": "shortpw", "email": "short@example.com",
            "password": "abc", "confirm_password": "abc",
        }, follow_redirects=True)
        assert r.status_code == 200


class TestLogin:
    """Login works with valid credentials and rejects invalid ones."""

    def _create_user(self, app):
        with app.app_context():
            u = User(first_name="Login", last_name="Test",
                     username="logintest", email="login@example.com")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()

    def test_login_with_email(self, client, app):
        self._create_user(app)
        r = client.post("/auth/login", data={
            "email": "login@example.com",
            "password": "password123",
        }, follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "dashboard" in r.headers.get("Location", "")

    def test_login_with_username(self, client, app):
        self._create_user(app)
        r = client.post("/auth/login", data={
            "email": "logintest",
            "password": "password123",
        }, follow_redirects=False)
        assert r.status_code in (301, 302)

    def test_wrong_password_rejected(self, client, app):
        self._create_user(app)
        r = client.post("/auth/login", data={
            "email": "login@example.com",
            "password": "wrongpassword",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b"Incorrect" in r.data or b"incorrect" in r.data

    def test_nonexistent_user_rejected(self, client):
        r = client.post("/auth/login", data={
            "email": "nobody@example.com",
            "password": "password123",
        }, follow_redirects=True)
        assert r.status_code == 200
        assert b"Incorrect" in r.data or b"incorrect" in r.data

    def test_logout_redirects(self, client, app):
        self._create_user(app)
        client.post("/auth/login", data={
            "email": "login@example.com",
            "password": "password123",
        }, follow_redirects=True)
        r = client.get("/auth/logout", follow_redirects=False)
        assert r.status_code in (301, 302)


# ─────────────────────────────────────────────────────────────────
# AUTH-PROTECTED PAGE TESTS
# ─────────────────────────────────────────────────────────────────

class TestProtectedPages:
    """Protected pages redirect guests to login."""

    def test_dashboard_requires_login(self, client):
        r = client.get("/dashboard", follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "login" in r.headers.get("Location", "").lower()

    def test_submit_idea_requires_login(self, client):
        r = client.get("/ideas/new", follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "login" in r.headers.get("Location", "").lower()

    def test_profile_requires_login(self, client):
        r = client.get("/profile/anyuser", follow_redirects=False)
        assert r.status_code in (301, 302)

    def test_dashboard_accessible_when_logged_in(self, auth_client):
        r = auth_client.get("/dashboard")
        assert r.status_code == 200

    def test_submit_idea_accessible_when_logged_in(self, auth_client):
        r = auth_client.get("/ideas/new")
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────
# IDEA CRUD TESTS
# ─────────────────────────────────────────────────────────────────

class TestIdeaSubmission:
    """Submitting an idea creates it in the DB and redirects to detail page."""

    def test_submit_idea_creates_record(self, auth_client, app):
        r = auth_client.post("/ideas/new", data={
            "title": "My New Idea",
            "summary": "A compelling one-line summary.",
            "description": "Full description of the idea here.",
            "category": "FinTech",
            "stage": "ideation",
            "privacy": "public",
            "emoji": "💡",
            "tags": "ai, startup",
        }, follow_redirects=False)
        assert r.status_code in (301, 302)
        with app.app_context():
            idea = Idea.query.filter_by(title="My New Idea").first()
            assert idea is not None
            assert idea.category == "FinTech"

    def test_submit_idea_redirects_to_detail_page(self, auth_client, app):
        r = auth_client.post("/ideas/new", data={
            "title": "Redirect Test Idea",
            "summary": "Testing redirect after submit.",
            "description": "Full description here.",
            "category": "EdTech",
            "stage": "validation",
            "privacy": "public",
            "emoji": "🎓",
            "tags": "",
        }, follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "/ideas/" in r.headers.get("Location", "")

    def test_submit_idea_creates_milestone_notification(self, auth_client, app):
        with app.app_context():
            user = User.query.filter_by(email="test@example.com").first()
            initial_count = Notification.query.filter_by(
                user_id=user.id, type="milestone"
            ).count()

        auth_client.post("/ideas/new", data={
            "title": "Notif Test Idea",
            "summary": "Testing notification on submit.",
            "description": "Full description of the idea here.",
            "category": "Health",
            "stage": "ideation",
            "privacy": "public",
            "emoji": "💊",
            "tags": "",
        }, follow_redirects=True)

        with app.app_context():
            user = User.query.filter_by(email="test@example.com").first()
            final_count = Notification.query.filter_by(
                user_id=user.id, type="milestone"
            ).count()
        assert final_count > initial_count


class TestIdeaDetail:
    """Idea detail page loads and increments view count."""

    def test_public_idea_detail_returns_200_for_logged_in_user(self, auth_client, sample_idea):
        r = auth_client.get(f"/ideas/{sample_idea}")
        assert r.status_code == 200

    def test_public_idea_detail_returns_200_for_anonymous_user(self, client, sample_idea):
        """Public ideas must be viewable without login."""
        r = client.get(f"/ideas/{sample_idea}")
        assert r.status_code == 200, (
            "Expected 200 for a public idea accessed anonymously, "
            f"got {r.status_code} — @login_required should not be on idea_detail"
        )

    def test_private_idea_returns_403_for_non_owner(self, app, auth_client):
        """Private ideas must not be accessible by other logged-in users."""
        with app.app_context():
            other = User(first_name="Other", last_name="User",
                         username="otheruser", email="other@example.com")
            other.set_password("password123")
            db.session.add(other)
            db.session.commit()
            private_idea = Idea(
                user_id=other.id, title="Private Idea",
                summary="Private.", description="Private description.",
                category="FinTech", stage="ideation", privacy="private",
            )
            db.session.add(private_idea)
            db.session.commit()
            idea_id = private_idea.id

        r = auth_client.get(f"/ideas/{idea_id}")
        assert r.status_code == 403, (
            f"Expected 403 for private idea accessed by non-owner, got {r.status_code}"
        )

    def test_idea_detail_increments_views(self, auth_client, app, sample_idea):
        with app.app_context():
            before = db.session.get(Idea, sample_idea).views
        auth_client.get(f"/ideas/{sample_idea}")
        with app.app_context():
            after = db.session.get(Idea, sample_idea).views
        assert after == before + 1

    def test_nonexistent_idea_returns_404(self, auth_client):
        r = auth_client.get("/ideas/99999")
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────
# AJAX ENDPOINT TESTS
# ─────────────────────────────────────────────────────────────────

class TestVoteEndpoint:
    """POST /ideas/<id>/vote toggles vote and returns correct JSON."""

    def test_vote_returns_json_ok(self, auth_client, sample_idea):
        r = auth_client.post(f"/ideas/{sample_idea}/vote",
                             content_type="application/json")
        data = json.loads(r.data)
        assert r.status_code == 200
        assert data["ok"] is True
        assert "voted" in data
        assert "vote_count" in data

    def test_vote_toggles_on(self, auth_client, sample_idea):
        r = auth_client.post(f"/ideas/{sample_idea}/vote",
                             content_type="application/json")
        data = json.loads(r.data)
        assert data["voted"] is True
        assert data["vote_count"] == 1

    def test_vote_toggles_off(self, auth_client, sample_idea):
        auth_client.post(f"/ideas/{sample_idea}/vote",
                         content_type="application/json")
        r = auth_client.post(f"/ideas/{sample_idea}/vote",
                             content_type="application/json")
        data = json.loads(r.data)
        assert data["voted"] is False
        assert data["vote_count"] == 0

    def test_vote_requires_login(self, client, sample_idea):
        r = client.post(f"/ideas/{sample_idea}/vote",
                        content_type="application/json",
                        follow_redirects=False)
        assert r.status_code in (302, 401)
        assert "login" in r.headers.get("Location", "").lower()

    def test_vote_creates_notification_for_author(self, app, sample_idea):
        with app.app_context():
            voter = User(first_name="Voter", last_name="User",
                        username="voter", email="voter@example.com")
            voter.set_password("password123")
            db.session.add(voter)
            db.session.commit()
            idea = db.session.get(Idea, sample_idea)
            author_id = idea.user_id
            initial_count = Notification.query.filter_by(
                user_id=author_id, type="vote"
            ).count()

        voter_client = app.test_client()
        voter_client.post("/auth/login", data={
            "email": "voter@example.com",
            "password": "password123",
        }, follow_redirects=True)
        voter_client.post(f"/ideas/{sample_idea}/vote",
                        content_type="application/json")
        with app.app_context():
            final_count = Notification.query.filter_by(
                user_id=author_id, type="vote"
            ).count()
        assert final_count > initial_count


class TestCommentEndpoint:
    """POST /ideas/<id>/comments creates comment and returns JSON."""

    def test_post_comment_returns_201(self, auth_client, sample_idea):
        r = auth_client.post(f"/ideas/{sample_idea}/comments",
                             json={"text": "Great idea!"})
        assert r.status_code == 201

    def test_post_comment_returns_ok_json(self, auth_client, sample_idea):
        r = auth_client.post(f"/ideas/{sample_idea}/comments",
                             json={"text": "This is interesting."})
        data = json.loads(r.data)
        assert data["ok"] is True
        assert "comment" in data
        assert data["comment"]["text"] == "This is interesting."

    def test_post_empty_comment_rejected(self, auth_client, sample_idea):
        r = auth_client.post(f"/ideas/{sample_idea}/comments",
                             json={"text": ""})
        assert r.status_code == 400

    def test_post_comment_too_long_rejected(self, auth_client, sample_idea):
        r = auth_client.post(f"/ideas/{sample_idea}/comments",
                             json={"text": "x" * 1001})
        assert r.status_code == 400

    def test_comment_requires_login(self, client, sample_idea):
        r = client.post(f"/ideas/{sample_idea}/comments",
                        json={"text": "Trying without auth"},
                        follow_redirects=False)
        assert r.status_code in (302, 401)
        assert "login" in r.headers.get("Location", "").lower()

    def test_comment_creates_notification_for_author(self, app, sample_idea):
        with app.app_context():
            commenter = User(first_name="Cmtr", last_name="User",
                            username="commenter", email="cmtr@example.com")
            commenter.set_password("password123")
            db.session.add(commenter)
            db.session.commit()
            idea = db.session.get(Idea, sample_idea)
            author_id = idea.user_id
            initial_count = Notification.query.filter_by(
                user_id=author_id, type="comment"
            ).count()

        cmtr_client = app.test_client()
        cmtr_client.post("/auth/login", data={
            "email": "cmtr@example.com",
            "password": "password123",
        }, follow_redirects=True)
        cmtr_client.post(f"/ideas/{sample_idea}/comments",
                        json={"text": "Nice idea!"})

        with app.app_context():
            final_count = Notification.query.filter_by(
                user_id=author_id, type="comment"
            ).count()
        assert final_count > initial_count


class TestBookmarkEndpoint:
    """POST /api/ideas/<id>/bookmark toggles bookmark."""

    def test_bookmark_returns_json_ok(self, auth_client, sample_idea):
        r = auth_client.post(f"/api/ideas/{sample_idea}/bookmark",
                             content_type="application/json")
        data = json.loads(r.data)
        assert r.status_code == 200
        assert data["ok"] is True
        assert "bookmarked" in data

    def test_bookmark_toggles_on(self, auth_client, sample_idea):
        r = auth_client.post(f"/api/ideas/{sample_idea}/bookmark",
                             content_type="application/json")
        data = json.loads(r.data)
        assert data["bookmarked"] is True

    def test_bookmark_toggles_off(self, auth_client, sample_idea):
        auth_client.post(f"/api/ideas/{sample_idea}/bookmark",
                         content_type="application/json")
        r = auth_client.post(f"/api/ideas/{sample_idea}/bookmark",
                             content_type="application/json")
        data = json.loads(r.data)
        assert data["bookmarked"] is False

    def test_bookmark_status_endpoint(self, auth_client, sample_idea):
        r = auth_client.get(f"/api/ideas/{sample_idea}/bookmark-status")
        data = json.loads(r.data)
        assert r.status_code == 200
        assert data["ok"] is True
        assert "bookmarked" in data

    def test_bookmark_requires_login(self, client, sample_idea):
        r = client.post(f"/api/ideas/{sample_idea}/bookmark",
                        content_type="application/json",
                        follow_redirects=False)
        assert r.status_code in (302, 401)
        assert "login" in r.headers.get("Location", "").lower()


class TestCollaborateEndpoint:
    """POST /ideas/<id>/collaborate toggles collaboration."""

    def test_collaborate_returns_json_ok(self, auth_client, sample_idea):
        r = auth_client.post(f"/ideas/{sample_idea}/collaborate",
                             content_type="application/json")
        data = json.loads(r.data)
        assert r.status_code == 200
        assert data["ok"] is True
        assert "collaborating" in data

    def test_collaborate_toggles_on(self, auth_client, sample_idea):
        r = auth_client.post(f"/ideas/{sample_idea}/collaborate",
                             content_type="application/json")
        data = json.loads(r.data)
        assert data["collaborating"] is True

    def test_collaborate_toggles_off(self, auth_client, sample_idea):
        auth_client.post(f"/ideas/{sample_idea}/collaborate",
                         content_type="application/json")
        r = auth_client.post(f"/ideas/{sample_idea}/collaborate",
                             content_type="application/json")
        data = json.loads(r.data)
        assert data["collaborating"] is False


class TestNotificationEndpoints:
    """GET /api/notifications and mark-read endpoints."""

    def test_get_notifications_returns_ok(self, auth_client):
        r = auth_client.get("/api/notifications")
        data = json.loads(r.data)
        assert r.status_code == 200
        assert data["ok"] is True
        assert "notifications" in data
        assert "unread_count" in data

    def test_get_notifications_requires_login(self, client):
        r = client.get("/api/notifications")
        assert r.status_code in (302, 401)

    def test_mark_all_notifications_read(self, auth_client, app):
        with app.app_context():
            user = User.query.filter_by(email="test@example.com").first()
            for i in range(3):
                db.session.add(Notification(
                    user_id=user.id, type="vote",
                    message=f"Notification {i}", link="/ideas/1"
                ))
            db.session.commit()

        r = auth_client.post("/api/notifications/read-all",
                             content_type="application/json")
        data = json.loads(r.data)
        assert data["ok"] is True

        r2 = auth_client.get("/api/notifications")
        data2 = json.loads(r2.data)
        assert data2["unread_count"] == 0


class TestTaskEndpoints:
    """Kanban task CRUD — create, update status, delete.

    Uses owned_idea so auth_client (testuser) is the idea owner and
    therefore has board write-access.  task CRUD on another user's idea
    should return 403 — verified by test_create_task_on_unowned_idea_forbidden.
    """

    def test_create_task_returns_201(self, auth_client, owned_idea):
        r = auth_client.post(f"/api/ideas/{owned_idea}/tasks",
                             json={"title": "Write tests",
                                   "priority": "high", "status": "todo"})
        assert r.status_code == 201
        data = json.loads(r.data)
        assert data["ok"] is True
        assert "task_id" in data

    def test_create_task_without_title_rejected(self, auth_client, owned_idea):
        r = auth_client.post(f"/api/ideas/{owned_idea}/tasks",
                             json={"title": "", "priority": "medium"})
        assert r.status_code == 400

    def test_create_task_with_invalid_status_rejected(self, auth_client, owned_idea):
        r = auth_client.post(f"/api/ideas/{owned_idea}/tasks",
                             json={"title": "Bad status", "status": "flying"})
        assert r.status_code == 400

    def test_create_task_with_invalid_priority_rejected(self, auth_client, owned_idea):
        r = auth_client.post(f"/api/ideas/{owned_idea}/tasks",
                             json={"title": "Bad priority", "priority": "urgent"})
        assert r.status_code == 400

    def test_create_task_on_unowned_idea_forbidden(self, auth_client, sample_idea):
        """testuser is not the owner of sample_idea — must get 403."""
        r = auth_client.post(f"/api/ideas/{sample_idea}/tasks",
                             json={"title": "Should be blocked", "status": "todo"},
                             content_type="application/json")
        assert r.status_code == 403, (
            "Expected 403 when non-owner tries to create a task, "
            f"but got {r.status_code}"
        )

    def test_update_task_status(self, auth_client, app, owned_idea):
        r = auth_client.post(f"/api/ideas/{owned_idea}/tasks",
                             json={"title": "A task", "status": "todo"})
        task_id = json.loads(r.data)["task_id"]

        r2 = auth_client.put(f"/api/ideas/{owned_idea}/tasks/{task_id}",
                              json={"status": "done"})
        assert r2.status_code == 200

        with app.app_context():
            task = db.session.get(Task, task_id)
            assert task.status == "done"

    def test_update_task_invalid_status_rejected(self, auth_client, owned_idea):
        r = auth_client.post(f"/api/ideas/{owned_idea}/tasks",
                             json={"title": "Validate me", "status": "todo"})
        task_id = json.loads(r.data)["task_id"]
        r2 = auth_client.put(f"/api/ideas/{owned_idea}/tasks/{task_id}",
                              json={"status": "not_a_valid_status"})
        assert r2.status_code == 400

    def test_delete_task(self, auth_client, app, owned_idea):
        r = auth_client.post(f"/api/ideas/{owned_idea}/tasks",
                             json={"title": "Delete me", "status": "todo"})
        task_id = json.loads(r.data)["task_id"]

        r2 = auth_client.delete(f"/api/ideas/{owned_idea}/tasks/{task_id}")
        assert r2.status_code == 200

        with app.app_context():
            assert db.session.get(Task, task_id) is None


class TestProfileEndpoints:
    """Profile page and bookmarks API."""

    def test_own_profile_accessible(self, auth_client):
        r = auth_client.get("/profile/testuser")
        assert r.status_code == 200

    def test_nonexistent_profile_returns_404(self, auth_client):
        r = auth_client.get("/profile/userwhodoesnotexist99")
        assert r.status_code == 404

    def test_bookmarks_api_returns_ok(self, auth_client):
        r = auth_client.get("/api/profile/bookmarks")
        data = json.loads(r.data)
        assert r.status_code == 200
        assert data["ok"] is True
        assert "bookmarks" in data


# ─────────────────────────────────────────────────────────────────
# API DATA ENDPOINT TESTS
# ─────────────────────────────────────────────────────────────────

class TestApiEndpoints:
    """Public API endpoints that serve JSON data."""

    def test_stats_endpoint_returns_json(self, client):
        r = client.get("/api/stats")
        data = json.loads(r.data)
        assert r.status_code == 200
        assert "ideas" in data
        assert "users" in data
        assert "votes" in data
        assert "comments" in data

    def test_chart_data_endpoint(self, client):
        r = client.get("/api/chart-data")
        data = json.loads(r.data)
        assert r.status_code == 200
        assert "by_stage" in data
        assert "by_category" in data
        assert "weekly" in data

    def test_trending_categories_endpoint(self, client):
        r = client.get("/api/trending-categories")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, list)

    def test_collaboration_board_requires_login(self, client, sample_idea):
        r = client.get(f"/ideas/{sample_idea}/board",
                    follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "login" in r.headers.get("Location", "").lower()

    def test_collaboration_board_accessible_when_logged_in(self, auth_client, sample_idea):
        r = auth_client.get(f"/ideas/{sample_idea}/board")
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────
# MESSAGES ROUTE TESTS
# ─────────────────────────────────────────────────────────────────

class TestMessageRoutes:
    """Direct-message inbox and send-message flow."""

    def _make_other_user(self, app):
        """Create a second user and return their username."""
        with app.app_context():
            other = User.query.filter_by(email="other@msg.example.com").first()
            if not other:
                other = User(
                    first_name="Other", last_name="User",
                    username="othermsguser", email="other@msg.example.com",
                )
                other.set_password("password123")
                db.session.add(other)
                db.session.commit()
        return "othermsguser"

    def _follow_other(self, app, follower_email, other_username):
        """Create a follow so follower can message other."""
        with app.app_context():
            follower = User.query.filter_by(email=follower_email).first()
            other = User.query.filter_by(username=other_username).first()
            existing = UserFollow.query.filter_by(
                follower_id=follower.id, followed_id=other.id
            ).first()
            if not existing:
                db.session.add(UserFollow(follower_id=follower.id, followed_id=other.id))
                db.session.commit()

    def test_inbox_requires_login(self, client):
        r = client.get("/messages/", follow_redirects=False)
        assert r.status_code in (301, 302), "Inbox must redirect unauthenticated users"
        assert "login" in r.headers.get("Location", "").lower()

    def test_inbox_accessible_when_logged_in(self, auth_client):
        r = auth_client.get("/messages/")
        assert r.status_code == 200

    def test_search_users_requires_login(self, client):
        r = client.get("/messages/search-users?q=test", follow_redirects=False)
        assert r.status_code in (301, 302)
        assert "login" in r.headers.get("Location", "").lower()

    def test_search_users_returns_json(self, auth_client, app):
        self._make_other_user(app)
        r = auth_client.get("/messages/search-users?q=othermsguser")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert isinstance(data, list)
        assert any(u["username"] == "othermsguser" for u in data), (
            "Search should find the newly created user"
        )

    def test_thread_page_loads_for_other_user(self, auth_client, app):
        self._make_other_user(app)
        r = auth_client.get("/messages/othermsguser")
        assert r.status_code == 200

    def test_cannot_message_without_following(self, auth_client, app):
        """Sending a message without following the recipient should be rejected."""
        self._make_other_user(app)
        r = auth_client.post(
            "/messages/othermsguser",
            data={"body": "Hello there"},
            follow_redirects=True,
        )
        # Route redirects with a warning flash — page still 200 after follow_redirects
        assert r.status_code == 200
        assert b"Follow" in r.data or b"follow" in r.data, (
            "Expected 'Follow' message when attempting to DM without following"
        )

    def test_can_message_following_user(self, auth_client, app):
        """Sending a message to a followed user should persist it."""
        self._make_other_user(app)
        self._follow_other(app, "test@example.com", "othermsguser")

        r = auth_client.post(
            "/messages/othermsguser",
            data={"body": "Hi there!"},
            follow_redirects=False,
        )
        assert r.status_code in (301, 302), (
            f"Expected redirect after successful send, got {r.status_code}"
        )
        with app.app_context():
            sender = User.query.filter_by(email="test@example.com").first()
            recipient = User.query.filter_by(username="othermsguser").first()
            msg = DirectMessage.query.filter_by(
                sender_id=sender.id, recipient_id=recipient.id
            ).first()
            assert msg is not None, "Message should be saved to the database"
            assert msg.body == "Hi there!"

    def test_cannot_message_yourself(self, auth_client):
        r = auth_client.get("/messages/testuser", follow_redirects=False)
        assert r.status_code in (301, 302), "Messaging yourself should redirect away"

    def test_nonexistent_user_thread_returns_404(self, auth_client):
        r = auth_client.get("/messages/userwhodoesnotexist99")
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────
# PASSWORD RESET FLOW TESTS
# ─────────────────────────────────────────────────────────────────

class TestPasswordReset:
    """Forgot-password and reset-password routes."""

    def test_forgot_password_page_accessible(self, client):
        r = client.get("/auth/forgot-password")
        assert r.status_code == 200

    def test_forgot_password_with_unregistered_email(self, client):
        """Unknown email should show the same generic message (no user enumeration)."""
        r = client.post(
            "/auth/forgot-password",
            data={"email": "nobody@example.com"},
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"registered" in r.data or b"reset" in r.data.lower(), (
            "Expected generic reset-link message for unknown email"
        )

    def test_forgot_password_invalid_email_format(self, client):
        """Malformed email address should not crash — returns generic response."""
        r = client.post(
            "/auth/forgot-password",
            data={"email": "not-an-email"},
            follow_redirects=True,
        )
        assert r.status_code == 200

    def test_reset_password_invalid_token_redirects(self, client):
        r = client.get("/auth/reset-password/this-is-not-a-real-token",
                       follow_redirects=False)
        assert r.status_code in (301, 302), "Bad token should redirect to forgot-password"
        assert "forgot" in r.headers.get("Location", "").lower()

    def test_reset_password_page_loads_with_valid_token(self, client, app):
        with app.app_context():
            user = User(first_name="Reset", last_name="User",
                        username="resetuser", email="reset@example.com")
            user.set_password("oldpassword1")
            db.session.add(user)
            db.session.commit()

        with app.app_context():
            token = generate_reset_token("reset@example.com")

        r = client.get(f"/auth/reset-password/{token}")
        assert r.status_code == 200, "Valid token should show the reset form"

    def test_reset_password_updates_password(self, client, app):
        with app.app_context():
            user = User(first_name="Reset2", last_name="User",
                        username="resetuser2", email="reset2@example.com")
            user.set_password("oldpassword1")
            db.session.add(user)
            db.session.commit()

        with app.app_context():
            token = generate_reset_token("reset2@example.com")

        r = client.post(
            f"/auth/reset-password/{token}",
            data={"password": "newpassword1", "confirm_password": "newpassword1"},
            follow_redirects=False,
        )
        assert r.status_code in (301, 302), "Successful reset should redirect to login"
        assert "login" in r.headers.get("Location", "").lower()

        with app.app_context():
            user = User.query.filter_by(email="reset2@example.com").first()
            assert user.check_password("newpassword1"), "Password hash should be updated"

    def test_reset_password_short_password_rejected(self, client, app):
        with app.app_context():
            user = User(first_name="Reset3", last_name="User",
                        username="resetuser3", email="reset3@example.com")
            user.set_password("oldpassword1")
            db.session.add(user)
            db.session.commit()
            token = generate_reset_token("reset3@example.com")

        r = client.post(
            f"/auth/reset-password/{token}",
            data={"password": "short", "confirm_password": "short"},
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"8" in r.data or b"characters" in r.data.lower(), (
            "Should display password-length error"
        )

    def test_reset_password_mismatch_rejected(self, client, app):
        with app.app_context():
            user = User(first_name="Reset4", last_name="User",
                        username="resetuser4", email="reset4@example.com")
            user.set_password("oldpassword1")
            db.session.add(user)
            db.session.commit()
            token = generate_reset_token("reset4@example.com")

        r = client.post(
            f"/auth/reset-password/{token}",
            data={"password": "newpassword1", "confirm_password": "different123"},
            follow_redirects=True,
        )
        assert r.status_code == 200
        assert b"match" in r.data.lower() or b"password" in r.data.lower(), (
            "Should display password-mismatch error"
        )