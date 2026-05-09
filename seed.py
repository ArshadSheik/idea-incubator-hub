"""
seed.py
Populates the database with sample users and ideas from seed_data/*.json.

Safe to re-run — wipes seed-controlled tables first.

Run with:  python seed.py
"""

import json
from pathlib import Path

from app import create_app
from models.models import (
    db, User, Idea, Vote, Comment, Tag, idea_tags,
    Bookmark, Notification, Collaboration, Task, UserFollow, IdeaMedia
)


# Resolve seed_data/ relative to this file so the script works regardless
# of where you run it from.
SEED_DATA_DIR = Path(__file__).parent / 'seed_data'


def load_json(filename):
    """Load and return the contents of a JSON file in seed_data/."""
    path = SEED_DATA_DIR / filename
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def wipe_existing_data():
    print('Wiping existing data...')
    db.session.execute(idea_tags.delete())
    IdeaMedia.query.delete()
    Notification.query.delete()
    Bookmark.query.delete()
    Task.query.delete()
    Collaboration.query.delete()
    Comment.query.delete()
    Vote.query.delete()
    UserFollow.query.delete()
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
    comments = [
        'Strong direction. I would test this with a small pilot first.',
        'Love this concept — what is the monetisation model?',
        'Have you validated this with real users yet?',
        'This solves a real pain point I have experienced myself.',
        'Who is the primary target audience here?',
        'Great execution on the pitch. Would love to collaborate.',
    ]
    for i, idea in enumerate(ideas_created):
        for u in users[: (i % len(users)) + 2]:
            if u.id != idea.user_id:
                db.session.add(Vote(user_id=u.id, idea_id=idea.id))
        commenters = [users[(i + 1) % len(users)], users[(i + 2) % len(users)]]
        for j, c in enumerate(commenters):
            if c.id != idea.user_id:
                db.session.add(Comment(
                    user_id=c.id,
                    idea_id=idea.id,
                    body=comments[(i + j) % len(comments)],
                ))
    db.session.commit()

def seed_bookmarks_and_notifications(users, ideas):
    """Seed bookmarks and notifications for each user."""
    print('Creating bookmarks and notifications...')
    for i, user in enumerate(users):
        bookmarkable = [idea for idea in ideas if idea.user_id != user.id]
        for idea in bookmarkable[i % max(len(bookmarkable), 1) : i % max(len(bookmarkable), 1) + 3]:
            db.session.add(Bookmark(user_id=user.id, idea_id=idea.id))
        for idea in ideas[:2]:
            db.session.add(Notification(
                user_id=user.id, type='vote',
                message=f"Someone upvoted your idea '{idea.title}'",
                link=f'/ideas/{idea.id}',
            ))
            db.session.add(Notification(
                user_id=user.id, type='comment',
                message=f"New comment on '{idea.title}'",
                link=f'/ideas/{idea.id}',
            ))
    db.session.commit()
    print('  ✓ Bookmarks and notifications seeded.')

def seed_collaborations(users, ideas):
    """Give each idea 2 accepted collaborators (not the author)."""
    print('Creating collaborations...')
    count = 0
    roles = ['contributor', 'reviewer', 'lead']
    for i, idea in enumerate(ideas):
        candidates = [u for u in users if u.id != idea.user_id]
        for j, user in enumerate(candidates[:2]):
            db.session.add(Collaboration(
                user_id=user.id,
                idea_id=idea.id,
                status='accepted',
                role=roles[j % len(roles)],
            ))
            count += 1
    db.session.commit()
    print(f'  ✓ {count} collaborations created.')


def seed_tasks(users, ideas):
    """Add 4 Kanban tasks per idea, assigned only to actual collaborators."""
    print('Creating tasks...')
    statuses   = ['todo', 'todo', 'in_progress', 'done']
    priorities = ['high', 'medium', 'medium', 'low']
    templates  = [
        ('Define target users',    'Write 3 user personas with pain points.'),
        ('Build MVP wireframes',    'Lo-fi sketches for the 3 core screens.'),
        ('Set up GitHub repo',      'Create repo, branch protection, CI workflow.'),
        ('Competitive analysis',    'Map out 5 existing solutions and their gaps.'),
        ('Draft landing page copy', 'Hero headline, 3 feature bullets, CTA.'),
        ('User interviews',         'Schedule and run 5 discovery calls.'),
        ('Tech stack decision',     'Evaluate options and document the choice.'),
        ('Pitch deck draft',        'Problem, solution, market size, team, ask.'),
    ]
    count = 0
    for i, idea in enumerate(ideas):
        # Only assign to accepted collaborators of this idea
        collab_user_ids = [
            c.user_id for c in
            Collaboration.query.filter_by(idea_id=idea.id, status='accepted').all()
        ]
        assignable = [u for u in users if u.id in collab_user_ids]
        # Fall back to idea author only if no collaborators
        if not assignable:
            assignable = [u for u in users if u.id == idea.user_id]

        for j in range(4):
            title, desc = templates[(i * 4 + j) % len(templates)]
            assignee = assignable[j % len(assignable)]
            db.session.add(Task(
                idea_id=idea.id,
                created_by=idea.user_id,
                assigned_to=assignee.id,
                title=title,
                description=desc,
                status=statuses[j],
                priority=priorities[j],
            ))
            count += 1
    db.session.commit()
    print(f'  ✓ {count} tasks created.')


def seed_follows(users):
    """Create a realistic follow graph — adjacent users follow each other."""
    print('Creating follows...')
    count = 0
    seen  = set()
    for i, follower in enumerate(users):
        for j, followed in enumerate(users):
            if follower.id == followed.id:
                continue
            if abs(i - j) > 2:
                continue
            key = (follower.id, followed.id)
            if key in seen:
                continue
            seen.add(key)
            db.session.add(UserFollow(follower_id=follower.id, followed_id=followed.id))
            count += 1
    db.session.commit()
    print(f'  ✓ {count} follow relationships created.')

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
        all_users = list(users_by_username.values())
        seed_collaborations(all_users, ideas_created)
        seed_tasks(all_users, ideas_created)
        seed_follows(all_users)
        seed_bookmarks_and_notifications(all_users, ideas_created)

        print('\nSeed complete.')
        print('Test login: username=jamie  password=password123')


if __name__ == '__main__':
    confirm = input('This will WIPE all data in the database. Type "yes" to continue: ')
    if confirm.strip().lower() == 'yes':
        seed()
    else:
        print('Aborted.')