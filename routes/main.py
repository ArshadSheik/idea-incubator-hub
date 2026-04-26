from flask import Blueprint, abort, redirect, render_template, url_for

main_bp = Blueprint("main", __name__)

IDEAS = {
    1: {
        "id": 1,
        "title": "Duolingo for musical instruments",
        "category": "EdTech",
        "stage": "Building",
        "stage_class": "building",
        "summary": "Learn guitar, piano, or drums in 5-min daily lessons with streaks, leaderboards, and real song unlocks.",
        "author": {"name": "Maya Kapoor", "initials": "MK"},
        "posted": "5 days ago",
        "views": "2.3k views",
        "votes": 312,
        "comments_total": 58,
        "collaborators_total": 9,
        "sections": {
            "idea": "A mobile-first learning app that teaches instruments using short daily drills, instant pitch/rhythm feedback, and game-like progression.",
            "problem": "Most instrument apps are either too beginner-only or too technical. Learners lose motivation quickly because progress feels slow and unclear.",
            "solution_intro": "Build a skill tree for each instrument and unlock songs as users master core techniques.",
            "solution_points": [
                "30-second ear training and rhythm warmups before each lesson",
                "AI feedback on timing and accuracy using microphone input",
                "Streaks, leagues, and friend challenges to keep consistency high",
                "Genre packs so users can learn songs they actually like",
            ],
        },
        "score": 92,
        "score_breakdown": {"market": 90, "support": 94, "feasibility": 86, "differentiation": 88},
        "tags": ["#music-tech", "#mobile-app", "#edtech", "#gamification"],
    },
    2: {
        "id": 2,
        "title": "AI-powered budget coach for Gen Z",
        "category": "FinTech",
        "stage": "Validation",
        "stage_class": "validation",
        "summary": "A no-judgment money buddy that roasts your spending in a fun way and helps you save without feeling restricted.",
        "author": {"name": "Jamie Liu", "initials": "JL"},
        "posted": "2 days ago",
        "views": "1.2k views",
        "votes": 247,
        "comments_total": 34,
        "collaborators_total": 6,
        "sections": {
            "idea": "A conversational coach that turns transactions into practical feedback, helping students build healthier spending habits without spreadsheet fatigue.",
            "problem": "Traditional budgeting apps feel like accounting tools and are hard to maintain for users who are just starting financial planning.",
            "solution_intro": "Use AI nudges, challenge-based saving, and pre-purchase checks to make daily money decisions easier.",
            "solution_points": [
                "Daily spending digest with tone-adjustable coaching",
                "Can-I-afford-it check before impulse purchases",
                "Weekly micro-goals with progress streak tracking",
                "Monthly recap in a visual summary users can share",
            ],
        },
        "score": 87,
        "score_breakdown": {"market": 92, "support": 88, "feasibility": 75, "differentiation": 81},
        "tags": ["#fintech", "#gen-z", "#ai", "#personal-finance"],
    },
    3: {
        "id": 3,
        "title": "Carbon-negative coffee subscription",
        "category": "GreenTech",
        "stage": "Ideation",
        "stage_class": "ideation",
        "summary": "Every bag offsets 2x its footprint via verified reforestation partners. Ethical bean sourcing baked in.",
        "author": {"name": "Sam Reyes", "initials": "SR"},
        "posted": "1 week ago",
        "views": "980 views",
        "votes": 189,
        "comments_total": 21,
        "collaborators_total": 3,
        "sections": {
            "idea": "A monthly coffee subscription that combines premium beans with transparent carbon accounting and local delivery optimization.",
            "problem": "Eco-conscious buyers struggle to verify whether sustainability claims are real or just marketing.",
            "solution_intro": "Bundle verified offset projects and publish lifecycle impact per order.",
            "solution_points": [
                "Per-bag carbon impact report visible in user dashboard",
                "Partner-only roasters with traceable sourcing",
                "Opt-in refill model to reduce packaging waste",
                "City-level delivery batching to reduce emissions",
            ],
        },
        "score": 74,
        "score_breakdown": {"market": 78, "support": 73, "feasibility": 70, "differentiation": 75},
        "tags": ["#greentech", "#subscription", "#sustainability", "#d2c"],
    },
    4: {
        "id": 4,
        "title": "CodeReview buddy — pair with an expert in 30 min",
        "category": "DevTools",
        "stage": "Launched",
        "stage_class": "launched",
        "summary": "Get 30 minutes of structured code review from verified senior engineers. Pay per session, no retainer.",
        "author": {"name": "Jamie Liu", "initials": "JL"},
        "posted": "3 weeks ago",
        "views": "3.1k views",
        "votes": 418,
        "comments_total": 71,
        "collaborators_total": 4,
        "sections": {
            "idea": "An on-demand review marketplace where developers book short, focused sessions with vetted senior engineers.",
            "problem": "Freelancers and indie teams often ship without proper peer review, leading to bugs and slow learning loops.",
            "solution_intro": "Provide fast booking, structured review templates, and action-focused takeaways.",
            "solution_points": [
                "Session prep form to define scope before call",
                "Language- and framework-specific reviewer matching",
                "Post-session issue checklist and code recommendations",
                "Performance and security review add-on options",
            ],
        },
        "score": 91,
        "score_breakdown": {"market": 89, "support": 93, "feasibility": 92, "differentiation": 84},
        "tags": ["#devtools", "#code-review", "#marketplace", "#saas"],
    },
    5: {
        "id": 5,
        "title": "3-minute mindfulness breaks during video calls",
        "category": "Health",
        "stage": "Validation",
        "stage_class": "validation",
        "summary": "A Chrome extension that suggests guided breathing between your back-to-back meetings. Stop burning out.",
        "author": {"name": "Priya Ahmed", "initials": "PA"},
        "posted": "3 days ago",
        "views": "890 views",
        "votes": 203,
        "comments_total": 45,
        "collaborators_total": 5,
        "sections": {
            "idea": "A browser extension that detects meeting load and nudges users into short guided resets between calls.",
            "problem": "Remote workers often go meeting-to-meeting without breaks, causing attention fatigue and stress build-up.",
            "solution_intro": "Detect schedule intensity and trigger short interventions at the right moments.",
            "solution_points": [
                "Auto-suggest 60/120/180 second micro-breaks",
                "Audio-only breathing guides for privacy",
                "Calendar-aware timing to avoid interruption",
                "Personal burnout trend chart for weekly reflection",
            ],
        },
        "score": 83,
        "score_breakdown": {"market": 84, "support": 86, "feasibility": 82, "differentiation": 80},
        "tags": ["#healthtech", "#remote-work", "#wellness", "#productivity"],
    },
    6: {
        "id": 6,
        "title": "StudyRooms: virtual library for focus sessions",
        "category": "Productivity",
        "stage": "Building",
        "stage_class": "building",
        "summary": "Body-doubling rooms where students join a silent video session to hold each other accountable. Pomodoro built-in.",
        "author": {"name": "Taylor Wong", "initials": "TW"},
        "posted": "3 days ago",
        "views": "1.6k views",
        "votes": 198,
        "comments_total": 42,
        "collaborators_total": 3,
        "sections": {
            "idea": "A focus platform that recreates library energy online by pairing silent co-study rooms with lightweight productivity tools.",
            "problem": "Students studying alone online often struggle with consistency and distraction without social accountability.",
            "solution_intro": "Use virtual rooms, timer cycles, and peer presence to improve completion rates.",
            "solution_points": [
                "Silent room presets by exam type or subject",
                "Built-in Pomodoro with synchronized timers",
                "Goal declaration at session start",
                "Session recap with completed task count",
            ],
        },
        "score": 82,
        "score_breakdown": {"market": 81, "support": 85, "feasibility": 84, "differentiation": 76},
        "tags": ["#students", "#focus", "#study", "#productivity"],
    },
    7: {
        "id": 7,
        "title": "Plant swap marketplace for apartment dwellers",
        "category": "Social",
        "stage": "Ideation",
        "stage_class": "ideation",
        "summary": "Trade, rescue, or adopt houseplants with people in your building or suburb. Verified ID + community reviews.",
        "author": {"name": "Jamie Liu", "initials": "JL"},
        "posted": "1 week ago",
        "views": "230 views",
        "votes": 89,
        "comments_total": 12,
        "collaborators_total": 1,
        "sections": {
            "idea": "A local community app for plant lovers to trade cuttings, rescue neglected plants, and share care tips.",
            "problem": "Most plant communities are broad and non-local, making safe and convenient exchanges difficult.",
            "solution_intro": "Match nearby users and simplify pickup logistics with trust signals.",
            "solution_points": [
                "Distance-based matching for quick local swaps",
                "Plant health checklist before listing",
                "Community reputation and trade history",
                "Seasonal care reminder feed by species",
            ],
        },
        "score": 68,
        "score_breakdown": {"market": 66, "support": 71, "feasibility": 74, "differentiation": 62},
        "tags": ["#community", "#marketplace", "#lifestyle", "#plants"],
    },
    8: {
        "id": 8,
        "title": "Splitwise but for recurring group bills",
        "category": "FinTech",
        "stage": "Ideation",
        "stage_class": "ideation",
        "summary": "Automate subscription splits (Netflix, Spotify, rent) with smart reminders and payment integration.",
        "author": {"name": "Riley Chen", "initials": "RC"},
        "posted": "6 days ago",
        "views": "410 views",
        "votes": 134,
        "comments_total": 22,
        "collaborators_total": 2,
        "sections": {
            "idea": "A recurring-bill coordinator that automates monthly splits and prevents one friend from always paying first.",
            "problem": "Manual reminders for shared subscriptions and rent are repetitive and often create awkward follow-ups.",
            "solution_intro": "Track recurring charges and automate due reminders for each group member.",
            "solution_points": [
                "Recurring templates for rent, utilities, and subscriptions",
                "Auto-reminders tied to due dates",
                "Late payment indicators and payment history",
                "One-tap split recalculation when members change",
            ],
        },
        "score": 77,
        "score_breakdown": {"market": 82, "support": 76, "feasibility": 79, "differentiation": 70},
        "tags": ["#fintech", "#shared-expenses", "#payments", "#b2c"],
    },
    9: {
        "id": 9,
        "title": "Hyper-local art commissions marketplace",
        "category": "Creator",
        "stage": "Validation",
        "stage_class": "validation",
        "summary": "Commission artists from your city and avoid long shipping times with local fulfillment.",
        "author": {"name": "Alex Garcia", "initials": "AG"},
        "posted": "4 days ago",
        "views": "845 views",
        "votes": 156,
        "comments_total": 28,
        "collaborators_total": 2,
        "sections": {
            "idea": "A city-based platform connecting customers with nearby artists for custom commissions and local pickups.",
            "problem": "Global platforms are crowded and slow for buyers who want local art and direct communication.",
            "solution_intro": "Prioritize location, style fit, and milestone-based commission workflows.",
            "solution_points": [
                "Artist discovery by neighborhood and art style",
                "Milestone escrow to protect both sides",
                "Commission timeline tracker with updates",
                "Local pickup and delivery coordination tools",
            ],
        },
        "score": 79,
        "score_breakdown": {"market": 80, "support": 78, "feasibility": 77, "differentiation": 81},
        "tags": ["#creator-economy", "#marketplace", "#local", "#art"],
    },
}

TEAM_POOL = [
    {"name": "Jamie Liu", "initials": "JL", "role": "Owner · Founder", "avatar_class": "avatar-1"},
    {"name": "Maya Kapoor", "initials": "MK", "role": "Backend dev", "avatar_class": "avatar-2"},
    {"name": "Sam Reyes", "initials": "SR", "role": "Designer", "avatar_class": "avatar-3"},
    {"name": "Priya Ahmed", "initials": "PA", "role": "Marketing", "avatar_class": "avatar-4"},
    {"name": "Taylor Wong", "initials": "TW", "role": "Product", "avatar_class": "avatar-5"},
    {"name": "Alex Garcia", "initials": "AG", "role": "iOS dev", "avatar_class": "avatar-6"},
]

CATEGORY_TAG_CLASS = {
    "FinTech": "tag-brand",
    "EdTech": "tag-violet",
    "GreenTech": "tag-mint",
    "DevTools": "tag-dark",
    "Health": "tag-pink",
    "Productivity": "tag-blue",
    "Social": "tag-mint",
    "Creator": "tag-yellow",
}

AUTHOR_AVATAR_CLASS = {member["name"]: member["avatar_class"] for member in TEAM_POOL}

for idea in IDEAS.values():
    idea["tag_class"] = CATEGORY_TAG_CLASS.get(idea["category"], "tag-brand")
    idea["author"]["avatar_class"] = AUTHOR_AVATAR_CLASS.get(idea["author"]["name"], "avatar-1")
    idea["collaborators"] = TEAM_POOL[: idea["collaborators_total"]]
    idea["discussion_preview"] = [
        {
            "name": "Maya Kapoor",
            "initials": "MK",
            "avatar_class": "avatar-2",
            "time": "1 day ago",
            "text": f"Strong direction for '{idea['title']}'. I would test this with a 20-user pilot first to validate retention.",
            "likes": 12,
        },
        {
            "name": "Sam Reyes",
            "initials": "SR",
            "avatar_class": "avatar-3",
            "time": "1 day ago",
            "text": "The value proposition is clear. I would tighten onboarding and show expected outcomes in week one.",
            "likes": 8,
        },
        {
            "name": "Priya Ahmed",
            "initials": "PA",
            "avatar_class": "avatar-4",
            "time": "2 days ago",
            "text": "Looks promising. Consider what your strongest differentiation is versus existing alternatives.",
            "likes": 15,
        },
    ]


@main_bp.app_errorhandler(404)
def page_not_found(_error):
    return render_template("404.html"), 404


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/index.html")
def index_html():
    return redirect(url_for("main.index"))


@main_bp.route("/explore.html")
def explore_html():
    return redirect(url_for("main.explore"))


@main_bp.route("/dashboard.html")
def dashboard_html():
    return redirect(url_for("main.dashboard"))


@main_bp.route("/idea-detail.html")
def idea_detail_html():
    return redirect(url_for("main.idea_detail", idea_id=2))


@main_bp.route("/idea_detail.html")
def idea_detail_legacy_html():
    return redirect(url_for("main.idea_detail", idea_id=2))


@main_bp.route("/about.html")
def about_html():
    return render_template("explore.html", ideas=IDEAS.values())


@main_bp.route("/login")
def login():
    return render_template("login.html")


@main_bp.route("/auth/login")
def auth_login():
    return redirect(url_for("main.login"))


@main_bp.route("/login.html")
def login_html():
    return redirect(url_for("main.login"))


@main_bp.route("/register")
def register():
    return render_template("register.html")


@main_bp.route("/auth/register")
def auth_register():
    return redirect(url_for("main.register"))


@main_bp.route("/register.html")
def register_html():
    return redirect(url_for("main.register"))


@main_bp.route("/explore")
def explore():
    return render_template("explore.html", ideas=IDEAS.values())


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/ideas/<int:idea_id>")
def idea_detail(idea_id: int):
    idea = IDEAS.get(idea_id)
    if idea is None:
        abort(404)
    return render_template("idea_detail.html", idea=idea)

@main_bp.route("/ideas/<int:idea_id>/collaborate")
def collaborate_idea(idea_id: int):
    idea = IDEAS.get(idea_id)
    if idea is None:
        abort(404)
    return redirect(url_for("main.idea_detail", idea_id=idea_id))
