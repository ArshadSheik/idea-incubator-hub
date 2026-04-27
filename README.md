# Idea Incubator Hub

A web platform where users share startup ideas, receive community feedback through votes and comments, collaborate on a Kanban board, and track each idea's progress from concept to launch.

Built for **CITS3403 / CITS5505 — Agile Web Development** at the University of Western Australia, Semester 1 2026.

---

## Team members

| UWA ID   | Name         | GitHub username |
|----------|--------------|-----------------|
| 25101735 | Arshad Sheik | @ArshadSheik    |
| 25003723 | Cong Yuan    | @ycong1129      |
| 24679419 | Dong Bo      | @DONG-BO-ERIC   |
| 24194729 | Yitian Kong  | @TomKongYT      |

---

## Tech stack

- **Backend:** Flask 3, Flask-SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate
- **Database:** SQLite via SQLAlchemy
- **Frontend:** HTML5, Bootstrap 5.3, custom CSS, jQuery, AJAX
- **Testing:** pytest (unit), Selenium (end-to-end)

---

## How to launch the application

### First-time setup (run these once after cloning)

#### 1. Clone the repo
```bash
git clone https://github.com/<your-org>/idea-incubator-hub.git
cd idea-incubator-hub
```

#### 2. Install dependencies
```bash
pip install -r requirements.txt
```

#### 3. Create your `.env` file
Add `SECRET_KEY`, `DATABASE_URL`, `FLASK_APP`, and `FLASK_ENV` in the project root. Generate a secret key with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 4. Initialise the database
```bash
python -m flask db upgrade
```

#### 5. Load sample data (run **once**)
```bash
python seed.py
```
> ⚠️ This wipes existing DB data and reloads from `seed_data/*.json`. Only run again if you want to reset to the sample dataset — otherwise you'll lose anything created through the website.

The seed script creates 6 users (password `password123` for all) and 8 sample ideas.

---

### Every time you want to run the app

After the first-time setup, your normal workflow is just:

```bash
python -m flask db upgrade   # applies any new migrations from teammates
python run.py                # starts the server
```

The app is available at **http://127.0.0.1:5000**. Log in as `jamie` / `password123` to test authenticated views.

---

## How to run the tests

Tests are added incrementally as features land. To run whatever is currently in `tests/`:
```bash
python -m pytest tests/ -v
```

---

## Project structure

```
idea-incubator-hub/
├── app.py              # Application factory
├── config.py           # Dev / Test / Production configs
├── run.py              # Entry point
├── seed.py             # Populates DB with sample data
├── seed_data/          # JSON fixtures used by seed.py
├── models/             # SQLAlchemy models
├── routes/             # Flask blueprints
├── templates/          # Jinja2 templates extending base.html
├── static/css/         # Per-page stylesheets
├── static/js/          # Per-page JS, includes AJAX handlers
├── tests/              # pytest unit + Selenium tests
├── migrations/         # Flask-Migrate schema versions
└── requirements.txt
```
