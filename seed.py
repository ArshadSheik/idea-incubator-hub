"""
seed.py
Populates the database with sample users and ideas from seed_data/*.json.

Safe to re-run — wipes seed-controlled tables first.

Run with:  python seed.py
"""

import json
import random
from pathlib import Path

from app import create_app
from models.models import (
    db, User, Idea, Vote, Comment, Tag, idea_tags,
    Bookmark, Notification, Collaboration, Task, UserFollow, IdeaMedia
)

SEED_DATA_DIR = Path(__file__).parent / 'seed_data'

# 30 varied startup-feedback comment templates
COMMENTS = [
    'Strong direction. I would test this with a small pilot first.',
    'Love this concept — what is the monetisation model?',
    'Have you validated this with real users yet?',
    'This solves a real pain point I have experienced myself.',
    'Who is the primary target audience here?',
    'Great execution on the pitch. Would love to collaborate.',
    'The biggest challenge I see is user acquisition — how are you thinking about that?',
    'Have you looked at what competitors are doing in this space?',
    'I think the freemium angle is the right call for early traction.',
    'This is exactly what I was looking for. When does it launch?',
    'The unit economics need more thought — what does CAC look like at scale?',
    'Really impressed by how clearly the problem is defined here.',
    'I would push harder on the differentiation angle — what makes this 10x better?',
    'Have you considered a B2B pivot? Enterprises would pay a lot for this.',
    'The timing is perfect — this trend is only accelerating.',
    'Great idea but the regulatory landscape can be tricky here. Have you mapped it out?',
    'Would love to see user research backing this up. Any discovery interviews done?',
    'The MVP scope looks right — resist the urge to over-build before validating.',
    'Interesting take. I wonder if a subscription model works better than one-time payment.',
    'Network effects could be powerful here if you get the initial flywheel spinning.',
    'This is very similar to something I tried last year. Happy to share lessons learned.',
    'The bottleneck is going to be supply side — how do you incentivise early contributors?',
    'Would this work in markets outside Australia? The TAM gets much bigger if so.',
    'The problem is clearly real. The question is whether people will pay to solve it.',
    'Have you thought about a waitlist to build pre-launch momentum?',
    'Solid foundations. The tech stack seems appropriate for the scale you are targeting.',
    'I flagged this for my co-founder — we have been thinking about the same problem.',
    'The description is compelling but the summary could be sharper. Lead with the outcome.',
    'This has viral loop potential if you add a referral mechanic early.',
    'Subscribed and watching closely. Please post updates as you validate this.',
]

COLLAB_MESSAGES = [
    'I have experience in this space and would love to contribute.',
    'This aligns perfectly with my background — keen to help push it forward.',
    'I can help with the technical side. Let me know if you want to chat.',
    'I have done user research in this area. Happy to share findings.',
    'I can bring design skills to this — the UX is critical for this type of product.',
    'I know potential early customers for this. Would love to make introductions.',
    'I have built something adjacent to this and can share what we learned.',
    'I can help with go-to-market strategy if that is useful at this stage.',
]

TASK_TEMPLATES = [
    ('Define target users',          'Write 3 user personas with pain points and jobs-to-be-done.'),
    ('Build MVP wireframes',          'Lo-fi sketches for the 3 core screens. Use Figma or pen and paper.'),
    ('Set up GitHub repo',            'Create repo, branch protection rules, and CI workflow.'),
    ('Competitive analysis',          'Map out 5 existing solutions and their key gaps.'),
    ('Draft landing page copy',       'Hero headline, 3 feature bullets, and a clear CTA.'),
    ('User interviews',               'Schedule and run 5 discovery calls with target users.'),
    ('Tech stack decision',           'Evaluate options and document the choice with rationale.'),
    ('Pitch deck draft',              'Problem, solution, market size, team, and ask slides.'),
    ('Set up analytics',              'Instrument key events with Mixpanel or PostHog.'),
    ('Write onboarding email flow',   'Welcome, activation, and day-7 re-engagement emails.'),
    ('Prototype core feature',        'Clickable prototype of the main user journey for testing.'),
    ('Define pricing model',          'Research comparable products and set initial pricing tiers.'),
    ('Legal and compliance check',    'Identify any regulatory requirements or risks early.'),
    ('SEO keyword research',          'Map search intent and keyword volume for the core use case.'),
    ('Set up staging environment',    'Mirror production environment for safe pre-release testing.'),
    ('Community launch post',         'Draft Reddit, HN, and Product Hunt launch copy.'),
    ('Build email waitlist',          'Set up a simple landing page with email capture and autoresponder.'),
    ('Define success metrics',        'Agree on the 3 core KPIs for the first 90 days.'),
]


def load_json(filename):
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
    """Every non-author votes; 4-5 comments per idea from different users."""
    print('Creating votes and comments...')
    users = list(users_by_username.values())
    vote_count = 0
    comment_count = 0

    for i, idea in enumerate(ideas_created):
        non_authors = [u for u in users if u.id != idea.user_id]

        # All non-authors vote (occasionally skip one for realism)
        voters = non_authors if len(non_authors) <= 3 else non_authors[:-1]
        for u in voters:
            db.session.add(Vote(user_id=u.id, idea_id=idea.id))
            vote_count += 1

        # 4-5 comments per idea, rotating through users and comment pool
        num_comments = min(len(non_authors), 5 if i % 3 != 0 else 4)
        for j in range(num_comments):
            commenter = non_authors[j % len(non_authors)]
            body = COMMENTS[(i * 7 + j * 4) % len(COMMENTS)]
            db.session.add(Comment(
                user_id=commenter.id,
                idea_id=idea.id,
                body=body,
            ))
            comment_count += 1

    db.session.commit()
    print(f'   {vote_count} votes and {comment_count} comments created.')


def seed_bookmarks_and_notifications(users, ideas):
    print('Creating bookmarks and notifications...')
    for i, user in enumerate(users):
        bookmarkable = [idea for idea in ideas if idea.user_id != user.id]
        # Each user bookmarks ~5 ideas they didn't write
        num_bookmarks = min(len(bookmarkable), 5)
        for idea in bookmarkable[:num_bookmarks]:
            db.session.add(Bookmark(user_id=user.id, idea_id=idea.id))

        # Notification for each of their own ideas
        own_ideas = [idea for idea in ideas if idea.user_id == user.id]
        for idea in own_ideas:
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
    print('   Bookmarks and notifications seeded.')


def seed_collaborations(users, ideas):
    """Give each idea 3-4 accepted collaborators with a request message."""
    print('Creating collaborations...')
    count = 0
    roles = ['contributor', 'reviewer', 'lead', 'designer', 'researcher']
    for i, idea in enumerate(ideas):
        candidates = [u for u in users if u.id != idea.user_id]
        # 3 or 4 collaborators per idea, alternating
        num_collabs = 4 if i % 2 == 0 else 3
        num_collabs = min(num_collabs, len(candidates))
        for j, user in enumerate(candidates[:num_collabs]):
            db.session.add(Collaboration(
                user_id=user.id,
                idea_id=idea.id,
                status='accepted',
                role=roles[j % len(roles)],
                message=COLLAB_MESSAGES[(i + j) % len(COLLAB_MESSAGES)],
            ))
            count += 1
    db.session.commit()
    print(f'   {count} collaborations created.')


def seed_tasks(users, ideas):
    """Add 6 Kanban tasks per idea, spread across todo/in_progress/done."""
    print('Creating tasks...')
    statuses   = ['todo', 'todo', 'in_progress', 'in_progress', 'done', 'done']
    priorities = ['high', 'medium', 'high', 'medium', 'low', 'medium']
    count = 0

    for i, idea in enumerate(ideas):
        collab_user_ids = [
            c.user_id for c in
            Collaboration.query.filter_by(idea_id=idea.id, status='accepted').all()
        ]
        assignable = [u for u in users if u.id in collab_user_ids]
        if not assignable:
            assignable = [u for u in users if u.id == idea.user_id]

        for j in range(6):
            title, desc = TASK_TEMPLATES[(i * 6 + j) % len(TASK_TEMPLATES)]
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
    print(f'   {count} tasks created.')


def seed_follows(users):
    """Every user follows every other user — fully connected follow graph."""
    print('Creating follows...')
    count = 0
    for follower in users:
        for followed in users:
            if follower.id == followed.id:
                continue
            db.session.add(UserFollow(follower_id=follower.id, followed_id=followed.id))
            count += 1
    db.session.commit()
    print(f'   {count} follow relationships created.')


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
        print(f'  {len(all_users)} users | {len(ideas_created)} ideas | password: password123')
        print('Test logins: jamie / maya / sam / priya / taylor / alex  (all password123)')


if __name__ == '__main__':
    confirm = input('This will WIPE all data in the database. Type "yes" to continue: ')
    if confirm.strip().lower() == 'yes':
        seed()
    else:
        print('Aborted.')
