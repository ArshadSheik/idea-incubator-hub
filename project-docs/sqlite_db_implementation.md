# Database

## Setup

We are using SQLite with SQLAlchemy. The database file is created automatically
at `instance/app.db` when you run `flask db upgrade`. This file is gitignored
so each developer has their own local copy.

Flask-Migrate is used to manage schema changes. Think of it like Git but for
the database structure.

```bash
flask db upgrade      # apply existing migrations to create your local DB
```

---

## Models

All models are defined in `models/models.py`. The tables are:

- **User** - stores account info and a hashed password (never plain text)
- **Idea** - a startup idea posted by a user, with category, stage and scores
- **Vote** - records a user upvoting an idea (one vote per user per idea)
- **Comment** - a comment on an idea, supports replies via parent_id
- **Tag** - keyword tags attached to ideas (many-to-many)
- **Collaboration** - records a user joining an idea's team
- **Task** - a kanban task on an idea's collaboration board

---

## If you change a model

If you need to add or change a column, run:

```bash
flask db migrate -m "describe your change here"
flask db upgrade
```

Then commit the new file that appears in `migrations/versions/`. Everyone
else on the team runs `flask db upgrade` after pulling.

---

## What is still pending

The models exist but most routes don't query them yet. Each person needs
to connect their page's route to the relevant models:

- Yuan Cong - register saves a User, login checks the password hash
- Bo Dong - query Ideas from the DB and pass to the template
- Yitian Kong - query the logged-in user's Ideas
