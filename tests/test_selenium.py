"""
tests/test_selenium.py

Selenium end-to-end browser tests.
These test what a real user experiences in a browser — page rendering,
JavaScript interactions, form submissions, and redirects.

The live_app fixture starts the Flask server automatically on port 5001.
No manual server startup is needed:
    python -m pytest tests/test_selenium.py -v

Uses headless Chrome via webdriver-manager so no manual ChromeDriver install needed.
"""

import sys
import threading
import time
import pytest
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from app import create_app
from models.models import db, User, Idea

BASE_URL = "http://localhost:5001"
WAIT_TIMEOUT = 10


# ─────────────────────────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def live_app():
    if os.path.exists("selenium_test.db"):
        os.remove("selenium_test.db")

    application = create_app("testing")
    application.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///selenium_test.db"

    with application.app_context():
        db.engine.dispose()
        db.drop_all()
        db.create_all()

        user = User(
            first_name="Selenium", last_name="Tester",
            username="seluser", email="sel@example.com",
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        idea = Idea(
            user_id=user.id, title="Selenium Test Idea",
            summary="An idea for testing.", description="Full description here.",
            category="FinTech", stage="ideation", privacy="public",
        )
        db.session.add(idea)
        db.session.commit()

    thread = threading.Thread(
        target=lambda: application.run(port=5001, use_reloader=False, debug=False),
        daemon=True,
    )
    thread.start()
    time.sleep(2)  # one-time wait for the server to bind — not a test wait
    yield application

    with application.app_context():
        db.drop_all()

    if os.path.exists("selenium_test.db"):
        os.remove("selenium_test.db")


@pytest.fixture(scope="module")
def driver(live_app):
    """Headless Chrome driver — shared across all Selenium tests."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,800")
    _exe = "chromedriver.exe" if sys.platform == "win32" else "chromedriver"
    chrome_driver_path = os.path.join(
        os.path.dirname(ChromeDriverManager().install()),
        _exe
    )
    service = Service(chrome_driver_path)
    d = webdriver.Chrome(service=service, options=options)
    d.implicitly_wait(5)
    yield d
    d.quit()


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def wait_for(driver, locator, timeout=WAIT_TIMEOUT):
    """Wait for an element to be visible, then return it."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(locator),
        message=f"Element {locator} not visible after {timeout}s",
    )


def wait_for_present(driver, locator, timeout=WAIT_TIMEOUT):
    """Wait for an element to be in the DOM (not necessarily visible), then return it."""
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located(locator),
        message=f"Element {locator} not present in DOM after {timeout}s",
    )


def login(driver):
    """Ensure the Selenium test user (sel@example.com) is logged in.

    Visits home first to establish a clean browser state, then navigates to
    /auth/login. If already logged in Flask redirects away immediately.
    Otherwise fills the form and submits it via element.submit() — which
    triggers a native network-level form POST, bypassing any JS interception.
    """
    driver.get(f"{BASE_URL}/")  # clean browser state before login page
    driver.get(f"{BASE_URL}/auth/login")
    # Already logged in — Flask redirected us somewhere else
    if "/auth/login" not in driver.current_url:
        return

    # Wait for the form to be in the DOM before touching it
    wait_for_present(driver, (By.CSS_SELECTOR, "form.auth-form"))

    # Set values via JavaScript and call form.submit() natively.
    # This guarantees the values are in the DOM at submission time,
    # bypassing any timing issues with send_keys or element_to_be_clickable.
    driver.execute_script(
        """
        document.querySelector('input[name="email"]').value = arguments[0];
        document.querySelector('input[name="password"]').value = arguments[1];
        document.querySelector('form.auth-form').submit();
        """,
        "sel@example.com", "password123",
    )
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        lambda d: "/auth/login" not in d.current_url,
        message="Login did not redirect away from /auth/login within the timeout",
    )


# ─────────────────────────────────────────────────────────────────
# SELENIUM TESTS
# ─────────────────────────────────────────────────────────────────

class TestLandingPage:
    """Landing page renders correctly in a real browser."""

    def test_landing_page_title(self, driver, live_app):
        driver.get(BASE_URL)
        assert "Idea Incubator" in driver.title or "Idea Incubator" in driver.page_source, \
            "Page title or content should contain 'Idea Incubator'"

    def test_landing_page_has_hero_section(self, driver, live_app):
        driver.get(BASE_URL)
        hero = wait_for(driver, (By.CSS_SELECTOR, "section.hero, h1.hero-title, .hero-section"))
        assert hero.is_displayed(), \
            "Hero section (section.hero or h1.hero-title) should be visible on the landing page"

    def test_landing_page_has_login_link(self, driver, live_app):
        driver.get(BASE_URL)
        links = driver.find_elements(By.TAG_NAME, "a")
        hrefs = [link.get_attribute("href") or "" for link in links]
        assert any("login" in href.lower() for href in hrefs), \
            "Landing page must have at least one link pointing to /auth/login"

    def test_landing_page_has_register_link(self, driver, live_app):
        driver.get(BASE_URL)
        links = driver.find_elements(By.TAG_NAME, "a")
        hrefs = [link.get_attribute("href") or "" for link in links]
        assert any("register" in href.lower() for href in hrefs), \
            "Landing page must have at least one link pointing to /auth/register"


class TestRegistrationFlow:
    """A new user can register and land on the dashboard."""

    def test_register_new_user(self, driver, live_app):
        driver.get(f"{BASE_URL}/auth/register")
        wait_for_present(driver, (By.NAME, "first_name")).send_keys("Browser")
        driver.find_element(By.NAME, "last_name").send_keys("Tester")
        driver.find_element(By.NAME, "username").send_keys("browsertest1")
        driver.find_element(By.NAME, "email").send_keys("browser1@example.com")
        driver.find_element(By.NAME, "password").send_keys("password123")
        driver.find_element(By.NAME, "confirm_password").send_keys("password123")
        btn = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        driver.execute_script("arguments[0].click();", btn)
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.url_contains("/dashboard"),
            message="Registration should redirect to /dashboard after success",
        )
        assert "/dashboard" in driver.current_url, \
            f"Expected /dashboard after registration, got: {driver.current_url}"


class TestLoginFlow:
    """Registered user can log in; wrong credentials are rejected."""

    def test_login_with_valid_credentials(self, driver, live_app):
        # Ensure we start logged out — navigate to home, then to login
        driver.get(f"{BASE_URL}/")
        driver.get(f"{BASE_URL}/auth/login")
        # If already logged in, log out first so we can actually test the login flow
        if "/auth/login" not in driver.current_url:
            driver.get(f"{BASE_URL}/auth/logout")
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                lambda d: "/auth/login" not in d.current_url
            )
            driver.get(f"{BASE_URL}/auth/login")

        email_field = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.NAME, "email"))
        )
        email_field.clear()
        email_field.send_keys("sel@example.com")
        pwd_field = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.NAME, "password"))
        )
        pwd_field.send_keys("password123")
        btn = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        driver.execute_script("arguments[0].click();", btn)
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.url_contains("/dashboard"),
            message="Valid login should redirect to /dashboard",
        )
        assert "/dashboard" in driver.current_url, \
            f"Valid credentials should reach /dashboard, got: {driver.current_url}"

    def test_login_shows_error_on_wrong_password(self, driver, live_app):
        # Navigate directly to login page (if already logged in, log out first)
        driver.get(f"{BASE_URL}/auth/login")
        if "/auth/login" not in driver.current_url:
            driver.get(f"{BASE_URL}/auth/logout")
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                lambda d: "/auth/login" not in d.current_url
            )
            driver.get(f"{BASE_URL}/auth/login")

        email_field = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.NAME, "email"))
        )
        email_field.clear()
        email_field.send_keys("sel@example.com")
        pwd_field = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.NAME, "password"))
        )
        pwd_field.send_keys("wrongpassword")
        btn = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        driver.execute_script("arguments[0].click();", btn)
        # After failed login the email field reappears (page reloaded with errors)
        wait_for_present(driver, (By.NAME, "email"))
        assert "login" in driver.current_url.lower(), \
            f"Wrong password should keep user on login page, got: {driver.current_url}"
        assert "incorrect" in driver.page_source.lower() or \
               "invalid" in driver.page_source.lower(), \
            "Wrong password should display an error message on the login page"


class TestExplorePage:
    """Explore page loads and search works."""

    def test_explore_page_loads(self, driver, live_app):
        driver.get(f"{BASE_URL}/explore")
        wait_for(driver, (By.TAG_NAME, "body"))
        assert "explore" in driver.page_source.lower() or \
               "idea" in driver.page_source.lower(), \
            "Explore page should contain 'explore' or 'idea' in its content"

    def test_explore_page_has_search_input(self, driver, live_app):
        driver.get(f"{BASE_URL}/explore")
        try:
            search = wait_for(driver, (By.ID, "searchInput"))
            assert search.is_displayed(), \
                "Search input #searchInput should be visible on the explore page"
        except TimeoutException:
            # Fallback: accept any visible text/search input
            inputs = driver.find_elements(
                By.CSS_SELECTOR, "input[type='text'], input[type='search']"
            )
            assert len(inputs) > 0, \
                "Explore page must have a search input field (no #searchInput found, " \
                "and no generic text/search inputs found either)"

    def test_explore_search_filters_results(self, driver, live_app):
        driver.get(f"{BASE_URL}/explore?q=Selenium+Test+Idea")
        wait_for(driver, (By.TAG_NAME, "body"))
        assert "Selenium Test Idea" in driver.page_source, \
            "Searching for 'Selenium Test Idea' should display the seeded idea in results"


class TestIdeaDetailPage:
    """Idea detail page renders all sections."""

    def _login_and_go_to_idea(self, driver, live_app):
        with live_app.app_context():
            idea = Idea.query.filter_by(title="Selenium Test Idea").first()
            idea_id = idea.id

        login(driver)
        driver.get(f"{BASE_URL}/ideas/{idea_id}")
        wait_for(driver, (By.CSS_SELECTOR, "h1, .idea-header-card"))
        return idea_id

    def test_idea_detail_loads(self, driver, live_app):
        self._login_and_go_to_idea(driver, live_app)
        assert "Selenium Test Idea" in driver.page_source, \
            "Idea detail page should display the idea's title 'Selenium Test Idea'"


class TestSubmitIdeaForm:
    """Submit idea multi-step form works in browser."""

    def test_submit_idea_page_loads(self, driver, live_app):
        login(driver)
        driver.get(f"{BASE_URL}/ideas/new")
        step1 = wait_for(driver, (By.ID, "step1"))
        assert step1.is_displayed(), \
            "Step 1 of the submit idea form (#step1) should be visible on page load"

    def test_submit_idea_step1_visible(self, driver, live_app):
        login(driver)
        driver.get(f"{BASE_URL}/ideas/new")
        step1 = wait_for(driver, (By.ID, "step1"))
        assert step1.is_displayed(), \
            "Step 1 container (#step1) should be visible when the form first loads"
        step2 = wait_for_present(driver, (By.ID, "step2"))
        assert not step2.is_displayed(), \
            "Step 2 (#step2) should be hidden before the user completes Step 1"

    def test_submit_idea_step1_validation(self, driver, live_app):
        """Clicking Next without filling the title must not advance to Step 2."""
        login(driver)
        driver.get(f"{BASE_URL}/ideas/new")
        next_btn = wait_for(driver, (By.ID, "nextStep1"))
        driver.execute_script("arguments[0].click();", next_btn)
        # Step 1 must remain visible — validation should have blocked progression
        step1 = WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.ID, "step1")),
            message="Step 1 should remain visible when required fields are empty",
        )
        step2 = driver.find_element(By.ID, "step2")
        assert step1.is_displayed(), \
            "Step 1 should still be visible after clicking Next with an empty title"
        assert not step2.is_displayed(), \
            "Step 2 should not appear when Step 1 title validation fails"

    def test_submit_idea_navigate_to_step2(self, driver, live_app):
        login(driver)
        driver.get(f"{BASE_URL}/ideas/new")
        # Wait for step1 to be visible (confirms page is rendered and CSS applied)
        wait_for(driver, (By.ID, "step1"))
        # Fill all step1 fields via JavaScript so values are reliably set in the DOM
        driver.execute_script(
            """
            document.querySelector('[name="title"]').value = arguments[0];
            document.querySelector('[name="summary"]').value = arguments[1];
            document.querySelector('[name="category"]').value = arguments[2];
            """,
            "Browser Test Idea",
            "A summary long enough to pass validation for testing.",
            "FinTech",
        )
        next_btn = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.element_to_be_clickable((By.ID, "nextStep1"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_btn)
        driver.execute_script("arguments[0].click();", next_btn)
        step2 = WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.visibility_of_element_located((By.ID, "step2")),
            message="Step 2 should become visible after filling Step 1 and clicking Next",
        )
        assert step2.is_displayed(), \
            "After completing Step 1 and clicking Next, Step 2 (#step2) should be visible"


class TestDashboard:
    """Dashboard loads with content when logged in; redirects guests."""

    def test_dashboard_loads_when_logged_in(self, driver, live_app):
        login(driver)
        driver.get(f"{BASE_URL}/dashboard")
        wait_for(driver, (By.CSS_SELECTOR, ".stat-card, .dashboard-hero, #ideaTabs"))
        assert "dashboard" in driver.page_source.lower() or \
               "idea" in driver.page_source.lower(), \
            "Dashboard should show user ideas or dashboard-specific content when logged in"

    def test_dashboard_redirects_when_guest(self, driver, live_app):
        # Ensure logged out: navigate to login page and log out if needed
        driver.get(f"{BASE_URL}/auth/login")
        if "/auth/login" not in driver.current_url:
            driver.get(f"{BASE_URL}/auth/logout")
            WebDriverWait(driver, WAIT_TIMEOUT).until(
                lambda d: "/auth/login" not in d.current_url
            )
        driver.get(f"{BASE_URL}/dashboard")
        WebDriverWait(driver, WAIT_TIMEOUT).until(
            EC.url_contains("login"),
            message="Guest visiting /dashboard should be redirected to the login page",
        )
        assert "login" in driver.current_url.lower(), \
            f"Unauthenticated /dashboard access should redirect to login, got: {driver.current_url}"
