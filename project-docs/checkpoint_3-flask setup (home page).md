# Checkpoint 3 — Backend Setup (Main/Index page)

## Flask server serving pages with jinja templates

## What I have done

Set up the Flask backend so the app runs as a proper web server instead of static HTML files.

### Files added
- `app.py` — creates and configures the Flask app
- `config.py` — loads settings like SECRET_KEY from the `.env` file
- `run.py` — start the server with `python run.py`
- `requirements.txt` — all Python packages needed
- `.env.example` — template showing what the `.env` file should look like
- `models/models.py` — database models for all tables
- `routes/main.py` — Flask route for the home page
- `templates/base.html` — shared layout that all pages extend
- `templates/index.html` — home page converted to a Jinja template

### Files changed
- `assets/` renamed to `static/` — Flask requires this folder name to serve CSS and JS files
- All `href="assets/..."` references updated to `url_for('static', filename='...')` in templates

---

## Why assets/ was renamed to static/

Flask has a built-in convention where static files must live in a folder called `static/`. The old frontend used `assets/` which Flask doesn't recognise, so CSS and JS were not loading. Renaming the folder and updating all references in the templates fixed this.

---

## The .env file

Holds the app's secret key. Never committed to GitHub.

---

## Database Setup

The database is SQLite managed via Flask-Migrate. The first time the project is set up, run all three commands:

```bash
python -m flask db init
python -m flask db migrate -m "initial schema"
python -m flask db upgrade
```

What each one does:
- `python -m flask db init` — creates the `migrations/` folder. Only ever run once by the first person setting up the project.
- `python -m flask db migrate -m "initial schema"` — reads the models and generates a migration file describing what tables to create.
- `python -m flask db upgrade` — applies the migration and creates the actual `instance/app.db` database file with all tables.

The `migrations/` folder is committed to the repo so teammates do not need
to run the first two commands. They only need:

```bash
python -m flask db upgrade
```

---

## Running the app

```bash
# make sure you have .env file in your folder

pip install -r requirements.txt
python -m flask db upgrade
python run.py
```

Visit `http://127.0.0.1:5000`
