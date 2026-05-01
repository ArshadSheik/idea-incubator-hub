"""
seed.py
Populates the database with sample users and ideas from seed_data/*.json.

Safe to re-run — wipes seed-controlled tables first.

Run with:  python seed.py
"""

import json
from pathlib import Path

from app import create_app
from models.models import db, User, Idea, Vote, Comment, Tag, idea_tags, Bookmark, Notification


# Resolve seed_data/ relative to this file so the script works regardless
# of where you run it from.
SEED_DATA_DIR = Path(__file__).parent / 'seed_data'


def load_json(filename):
    """Load and return the contents of a JSON file in seed_data/."""
    path = SEED_DATA_DIR / filename
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def wipe_existing_data():
    """Delete in reverse FK order so SQLite doesn't complain."""
    print('Wiping existing data...')
    # Clear the idea_tags join table first — it isn't auto-cleared
    # when the parent Idea or Tag rows are deleted.
    db.session.execute(idea_tags.delete())
    Comment.query.delete()
    Vote.query.delete()
    Idea.query.delete()
    Tag.query.delete()
    User.query.delete()
    db.session.commit()


def create_users(sample_users):
    """Create sample users with a shared dev password."""
    print('Creating users...')
    users_by_username = {}
    for u in sample_users:
        user = User(**u)
        user.set_password('password123')
        db.session.add(user)
        users_by_username[u['username']] = user
    db.session.commit()
    print(f'   {len(users_by_username)} users created.')
    return users_by_username


def create_tags(sample_ideas):
    """Collect every tag name from the sample ideas and create them."""
    print('Creating tags...')
    all_tag_names = {t for idea in sample_ideas for t in idea['tags']}
    tags_by_name = {}
    for name in all_tag_names:
        tag = Tag(name=name)
        db.session.add(tag)
        tags_by_name[name] = tag
    db.session.commit()
    print(f'   {len(tags_by_name)} tags created.')
    return tags_by_name


def create_ideas(sample_ideas, users_by_username, tags_by_name):
    """Create ideas, resolving username -> user_id and tag names -> Tag objects."""
    print('Creating ideas...')
    ideas_created = []
    for entry in sample_ideas:
        data = entry.copy()
        tag_names = data.pop('tags')
        username  = data.pop('username')
        data['user_id'] = users_by_username[username].id
        idea = Idea(**data)
        idea.tags = [tags_by_name[n] for n in tag_names]
        db.session.add(idea)
        ideas_created.append(idea)
    db.session.commit()
    print(f'   {len(ideas_created)} ideas created.')
    return ideas_created


def create_votes_and_comments(users_by_username, ideas_created):
    """Sprinkle some votes and comments so the UI doesn't look empty."""
    print('Creating sample votes and comments...')
    users = list(users_by_username.values())
    for i, idea in enumerate(ideas_created):
        for u in users[: (i % len(users)) + 2]:
            if u.id != idea.user_id:
                db.session.add(Vote(user_id=u.id, idea_id=idea.id))
        commenters = [users[(i + 1) % len(users)], users[(i + 2) % len(users)]]
        for c in commenters:
            if c.id != idea.user_id:
                db.session.add(Comment(
                    user_id=c.id,
                    idea_id=idea.id,
                    body='Strong direction. I would test this with a small pilot first.',
                ))
    db.session.commit()

def seed_bookmarks_and_notifications(users, ideas):
    """Seed some bookmarks and notifications so profile/dashboard aren't empty."""
    if not users or not ideas:
        return

    # First user bookmarks the first 3 ideas
    for idea in ideas[:3]:
        existing = Bookmark.query.filter_by(user_id=users[0].id, idea_id=idea.id).first()
        if not existing:
            db.session.add(Bookmark(user_id=users[0].id, idea_id=idea.id))

    # Give first user some sample notifications
    notifs = [
        {"type": "vote",    "message": f"Someone upvoted '{ideas[0].title}'",       "link": f"/ideas/{ideas[0].id}"},
        {"type": "comment", "message": f"New comment on '{ideas[0].title}'",         "link": f"/ideas/{ideas[0].id}"},
        {"type": "collab",  "message": "Someone requested to join your idea team.",  "link": f"/ideas/{ideas[0].id}"},
    ]
    for n in notifs:
        db.session.add(Notification(
            user_id=users[0].id,
            type=n["type"],
            message=n["message"],
            link=n["link"],
        ))

    db.session.commit()
    print("  ✓ Bookmarks and notifications seeded")

def seed():
    sample_users = load_json('users.json')
    sample_ideas = load_json('ideas.json')

    app = create_app('development')
    with app.app_context():
        wipe_existing_data()
        users_by_username = create_users(sample_users)
        tags_by_name      = create_tags(sample_ideas)
        ideas_created     = create_ideas(sample_ideas, users_by_username, tags_by_name)
        create_votes_and_comments(users_by_username, ideas_created)

        print('\nSeed complete.')
        print('Test login -> username: jamie  password: password123')


if __name__ == '__main__':
    confirm = input('This will WIPE all data in the database. Type "yes" to continue: ')
    if confirm.strip().lower() == 'yes':
        seed()
    else:
        print('Aborted.')