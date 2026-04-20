# Backend Guide for the Team

## Getting started

Pull the latest `master` branch after the flask-setup PR is merged, then:

```bash
# make sure you have .env file (do this once, never commit it)
pip install -r requirements.txt
flask db upgrade
python run.py
```

Visit `http://127.0.0.1:5000` — the home page should load. If it does,
you are set up correctly.

---

## How the project is structured now

```
├── app.py              <- registers all blueprints
├── config.py           <- reads from .env
├── run.py              <- starts the server
├── models/models.py    <- all database models
├── routes/             <- one file per page/feature
├── templates/          <- all Jinja HTML templates
│   └── base.html       <- shared navbar and footer
└── static/             <- CSS, JS, images
```

---

## Adding your page (jinja template)

### 1. Create your branch off dev

```bash
git checkout dev
git pull origin dev
git checkout -b feature/your-page-backend
```

### 2. Build your route file in routes/

Create a new file e.g. `routes/explore.py`:

```python
from flask import Blueprint, render_template
from models.models import Idea

explore_bp = Blueprint('explore', __name__)

@explore_bp.route('/explore')
def explore():
    ideas = Idea.query.filter_by(privacy='public').all()
    return render_template('explore.html', ideas=ideas)
```

### 3. Register it in app.py

Open `app.py` and add two lines:

```python
from routes.explore import explore_bp
app.register_blueprint(explore_bp)
```

### 4. Convert your HTML page to a Jinja template

Move your existing HTML file into `templates/` and wrap it like this:

```html
{% extends "base.html" %}
{% block title %}Explore — IdeaHub{% endblock %}
{% block page_name %}explore{% endblock %}

{% block styles %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/explore.css') }}">
{% endblock %}

{% block content %}

  <!-- your existing HTML goes here -->
  <!-- replace hardcoded data with Jinja loops -->
  {% for idea in ideas %}
    <p>{{ idea.title }}</p>
  {% endfor %}

{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/explore.js') }}"></script>
{% endblock %}
```

The key things to change in your existing HTML:
- Remove the `<head>`, `<nav>` and `<footer>` — base.html already has them
- Change `href="assets/css/..."` to `url_for('static', filename='css/...')`
- Change `href="page.html"` links to `url_for('blueprint.function')`

---

## Important rules

**Static files** — always use `url_for`, never relative paths:
```html
<!-- wrong -->
<link href="../assets/css/main.css">

<!-- right -->
<link href="{{ url_for('static', filename='css/main.css') }}">
```

**Internal links** — use `url_for`:
```html
<a href="{{ url_for('explore.explore') }}">Explore</a>
<a href="{{ url_for('main.index') }}">Home</a>
```

**Protecting pages** — add `@login_required` if the page needs a logged-in user:
```python
from flask_login import login_required, current_user

@your_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
```

**Forms** — every form that submits data needs a CSRF token:
```html
<form method="POST">
  {{ form.hidden_tag() }}
  ...
</form>
```

---

## Team tasks

**Yuan Cong**
- Build `routes/auth.py` with login, register, logout routes
- Convert login and register HTML pages to Jinja templates in `templates/auth/`
- Save new users to the database, check password hash on login
- All forms need `{{ form.hidden_tag() }}` for CSRF

**Do Bong**
- Build `routes/explore.py` with a `/explore` route
- Query ideas from the database and replace hardcoded cards with a Jinja loop

**Yitian Kong**
- Add a `/dashboard` route (can go in `routes/main.py`)
- Add `@login_required` so logged-out users are redirected
- Query the current user's ideas with `Idea.query.filter_by(user_id=current_user.id)`
