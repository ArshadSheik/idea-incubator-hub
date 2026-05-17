# Test Documentation — Idea Incubator Hub

## Overview

| File | Type | Count |
|------|------|-------|
| `test_models.py` | Unit tests (model layer) | 8 |
| `test_routes.py` | Integration tests (route/HTTP layer) | 18 |
| `test_selenium.py` | Selenium end-to-end (real browser) | 17 |
| **Total** | | **43** |

### Run commands

```bash
# Unit + integration only (fast, no browser)
python -m pytest tests/test_models.py tests/test_routes.py -v

# Selenium only (server starts automatically — no second terminal needed)
python -m pytest tests/test_selenium.py -v

# Everything
python -m pytest tests/ -v
```

---

## Unit Tests — `test_models.py` (8 tests)

Tests the SQLAlchemy model layer in **complete isolation** using an in-memory SQLite database.
CSRF is disabled. Each test function gets a fresh database — fully independent.

Tests are written with multiple assertions per method to cover tightly related behaviours concisely.

### `TestUserAuth` — 3 tests
Verifies passwords are stored as salted hashes and authentication works correctly.

| Test | What it checks |
|------|----------------|
| `test_password_hashed_not_plaintext` | `password_hash` is not the raw string, and contains "pbkdf2" or "scrypt" (confirms Werkzeug salted hashing) |
| `test_correct_password_accepted` | `check_password("password123")` returns `True` |
| `test_wrong_password_rejected` | `check_password("wrong")` returns `False` |

### `TestUserProperties` — 1 test
Tests computed display properties on the User model.

| Test | What it checks |
|------|----------------|
| `test_display_name_and_initials` | `user.display_name` returns `"First Last"` and `user.initials` returns `"AS"` for Arshad Sheik |

### `TestIdeaCounts` — 2 tests
Tests computed counters on the Idea model and vote tracking.

| Test | What it checks |
|------|----------------|
| `test_vote_and_comment_counts` | New idea starts at 0 votes and 0 comments; both increment correctly after adding `Vote` and `Comment` rows |
| `test_has_voted_tracking` | `user.has_voted(idea)` returns `False` initially, then `True` after a `Vote` row is inserted |

### `TestUniqueConstraints` — 2 tests
Verifies database-level uniqueness constraints raise `IntegrityError` on violation.

| Test | What it checks |
|------|----------------|
| `test_duplicate_vote_raises_integrity_error` | Same user cannot cast two votes on the same idea |
| `test_duplicate_email_raises_integrity_error` | Two users cannot share the same email address |

---

## Integration Tests — `test_routes.py` (18 tests)

Tests the full HTTP request/response cycle using Flask's built-in test client.
Uses an in-memory SQLite database with CSRF disabled. Each test gets a fresh DB.

Tests cover 7 functional areas across the app.

### `TestPublicPages` — 2 tests
Pages accessible without authentication.

| Test | What it checks |
|------|----------------|
| `test_home_and_explore_accessible` | Both `/` and `/explore` return HTTP 200 for anonymous users |
| `test_unknown_route_returns_404` | An unknown URL returns HTTP 404 (custom error page is served) |

### `TestRegistration` — 2 tests
User registration flow and duplicate rejection.

| Test | What it checks |
|------|----------------|
| `test_register_creates_user_and_redirects_to_dashboard` | Valid POST creates the user in the DB and redirects to `/dashboard` |
| `test_duplicate_email_rejected` | Registering with an already-used email returns 200 with an error message |

### `TestLogin` — 3 tests
Login/logout flow.

| Test | What it checks |
|------|----------------|
| `test_login_valid_credentials_redirects_to_dashboard` | Valid credentials redirect to `/dashboard` |
| `test_wrong_password_shows_error` | Wrong password returns 200 with "Incorrect" error text |
| `test_logout_redirects` | `GET /auth/logout` redirects (301/302) |

### `TestAccessControl` — 3 tests
Authentication gating and privacy enforcement.

| Test | What it checks |
|------|----------------|
| `test_protected_pages_redirect_guests_to_login` | Both `/dashboard` and `/ideas/new` redirect unauthenticated users to login |
| `test_dashboard_accessible_when_logged_in` | Logged-in user gets HTTP 200 on `/dashboard` |
| `test_private_idea_returns_403_for_non_owner` | Non-owner accessing a private idea gets HTTP 403 |

### `TestIdeaFlow` — 2 tests
Idea submission and public viewing.

| Test | What it checks |
|------|----------------|
| `test_submit_idea_saves_to_db_and_redirects` | POST to `/ideas/new` saves the idea in the DB and redirects to `/ideas/<id>` |
| `test_public_idea_viewable_by_anonymous_user` | A public idea detail page returns HTTP 200 without login |

### `TestSocialInteractions` — 5 tests
Vote, comment, bookmark, and collaboration AJAX endpoints.

| Test | What it checks |
|------|----------------|
| `test_vote_toggle_on_and_off` | First POST votes (voted=True, count=1); second POST unvotes (voted=False, count=0) |
| `test_vote_requires_login` | Unauthenticated vote request returns 302 or 401 |
| `test_comment_created_and_empty_body_rejected` | Valid comment returns 201; empty body returns 400 |
| `test_bookmark_toggles_on_and_off` | First POST bookmarks (bookmarked=True); second POST removes it (bookmarked=False) |
| `test_collaborate_toggles_on_and_off` | First POST joins collaboration (collaborating=True); second POST leaves (collaborating=False) |

### `TestPasswordReset` — 1 test
Full password reset flow end-to-end in a single test.

| Test | What it checks |
|------|----------------|
| `test_full_reset_flow` | Valid token shows the reset form (200); invalid token redirects to forgot-password; successful reset redirects to login and the new password hash is saved in the DB |

---

## Selenium Tests — `test_selenium.py` (17 tests)

End-to-end browser tests using headless Chrome via `webdriver-manager`.

**Key design decisions:**
- The `live_app` fixture starts Flask on port 5001 in a background thread — **no manual `python run.py` needed**.
- Uses an isolated `selenium_test.db` file (created before tests, deleted after).
- Seeds one user (`seluser` / `password123`) and one idea (`"Selenium Test Idea"`) before tests run.
- The `driver` fixture is shared across the full module (one browser session, faster).

### `TestLandingPage` — 4 tests

| Test | What it checks |
|------|----------------|
| `test_landing_page_title` | Page title or content contains "Idea Incubator" |
| `test_landing_page_has_hero_section` | Hero section (`section.hero` or `h1.hero-title`) is visible |
| `test_landing_page_has_login_link` | At least one `<a>` href contains "login" |
| `test_landing_page_has_register_link` | At least one `<a>` href contains "register" |

### `TestRegistrationFlow` — 1 test

| Test | What it checks |
|------|----------------|
| `test_register_new_user` | Filling all registration fields and submitting redirects to `/dashboard` in a real browser |

### `TestLoginFlow` — 2 tests

| Test | What it checks |
|------|----------------|
| `test_login_with_valid_credentials` | Valid credentials redirect to `/dashboard` |
| `test_login_shows_error_on_wrong_password` | Wrong password keeps user on login page with an error message visible |

### `TestExplorePage` — 3 tests

| Test | What it checks |
|------|----------------|
| `test_explore_page_loads` | Page body contains "explore" or "idea" |
| `test_explore_page_has_search_input` | A search input (`#searchInput` or generic text input) is visible |
| `test_explore_search_filters_results` | Searching `?q=Selenium+Test+Idea` returns the seeded idea in results |

### `TestIdeaDetailPage` — 1 test

| Test | What it checks |
|------|----------------|
| `test_idea_detail_loads` | Idea detail page renders and displays the seeded idea's title |

### `TestSubmitIdeaForm` — 4 tests
Tests the multi-step idea submission form including JavaScript validation behaviour.

| Test | What it checks |
|------|----------------|
| `test_submit_idea_page_loads` | Step 1 (`#step1`) is visible on page load |
| `test_submit_idea_step1_visible` | Step 1 is visible and Step 2 is hidden on initial load |
| `test_submit_idea_step1_validation` | Clicking "Next" with an empty title does NOT advance to Step 2 (JS validation blocks it) |
| `test_submit_idea_navigate_to_step2` | Filling Step 1 fields and clicking "Next" makes Step 2 visible |

### `TestDashboard` — 2 tests

| Test | What it checks |
|------|----------------|
| `test_dashboard_loads_when_logged_in` | Dashboard content (`.stat-card` / `.dashboard-hero` / `#ideaTabs`) is visible when logged in |
| `test_dashboard_redirects_when_guest` | Unauthenticated visit to `/dashboard` redirects to the login page |
