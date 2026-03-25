# 🚀 Idea Incubator Hub — Checkpoint 2

## 📌 Application Overview

**Startup Idea Incubator Platform** - A web application where users can submit startup ideas, receive community feedback, collaborate with others, and track the growth and validation of their ideas over time. The platform can also include a market and risk analytics dashboard.

### Users Can:
1. Share innovative ideas
2. Get feedback through comments and votes
3. Collaborate with other users
4. Track how their idea evolves

---

## 👤 User Stories

### 🔐 Authentication

| # | User Story | Story Points |
|---|-----------|:------------:|
| 1 | As a user, I want to create an account so I can use the platform. | 3 |
| 2 | As a user, I want to log in and log out securely. | 2 |
| 3 | As a user, I want to reset my password so that I can regain access to my account if I forget it. | 3 |

### 💡 Idea Management

| # | User Story | Story Points |
|---|-----------|:------------:|
| 4 | As a user, I want to post a startup idea. | 3 |
| 5 | As a user, I want to view ideas posted by others. | 2 |
| 6 | As a user, I want to edit or delete my own ideas. | 3 |
| 7 | As a user, I want to track updates or progress of an idea. | 5 |

### 💬 Interaction

| # | User Story | Story Points |
|---|-----------|:------------:|
| 8 | As a user, I want to upvote or downvote ideas. | 2 |
| 9 | As a user, I want to comment on ideas to give feedback. | 3 |

### 🤝 Collaboration

| # | User Story | Story Points |
|---|-----------|:------------:|
| 10 | As a user, I want to join as a collaborator on an idea. | 5 |
| 11 | As a user, I want to see collaborators on an idea. | 2 |

### 🔍 Search & Discovery

| # | User Story | Story Points |
|---|-----------|:------------:|
| 12 | As a user, I want to search ideas by keywords or tags. | 5 |

### 👤 Profile

| # | User Story | Story Points |
|---|-----------|:------------:|
| 13 | As a user, I want to view my profile and my posted ideas. | 3 |

### 🔔 Notifications

| # | User Story | Story Points |
|---|-----------|:------------:|
| 14 | As a user, I want to receive notifications when someone comments on my idea so that I can respond quickly. | 8 |

---

## 🌐 Web Pages

### 1. Authentication Pages
- Login Page
- Signup Page

### 2. Main Pages
- Home / Explore Ideas
- Idea Details
- Submit Idea
- Edit Idea

### 3. Collaboration Pages
- Collaboration Board *(per idea)*
- Join / Leave Collaboration

### 4. User Pages
- Profile Page
- My Ideas Page
- Forgot Password / Reset Password Page

### 5. Utility Pages
- Search Results Page

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript |
| CSS Framework | Bootstrap |
| Interactivity | jQuery, AJAX |
| Backend | Flask (Python) |
| Authentication | Flask-Login |
| ORM | Flask-SQLAlchemy |
| Database | SQLite |
| Real-time *(optional)* | WebSockets |

---

## 🗄️ Database Schema

### User
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary Key |
| username | String | Unique |
| email | String | Unique |
| password_hash | String | |

### Idea
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary Key |
| title | String | |
| description | Text | |
| category | String | |
| created_at | DateTime | |
| user_id | Integer | Foreign Key → User |

### Vote
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key → User |
| idea_id | Integer | Foreign Key → Idea |
| vote_type | Integer | +1 or -1 |

### Comment
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary Key |
| content | Text | |
| created_at | DateTime | |
| user_id | Integer | Foreign Key → User |
| idea_id | Integer | Foreign Key → Idea |

### Collaboration
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key → User |
| idea_id | Integer | Foreign Key → Idea |
| role | String | Optional |

### Tag *(optional)*
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary Key |
| name | String | Unique |

### IdeaTag *(Many-to-Many)*
| Column | Type | Notes |
|--------|------|-------|
| idea_id | Integer | Foreign Key → Idea |
| tag_id | Integer | Foreign Key → Tag |

### Notification
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary Key |
| user_id | Integer | Foreign Key → User |
| message | String | |
| is_read | Boolean | |
| created_at | DateTime | |

---

## 👥 Team Members

| UWA ID | Name | GitHub Username |
|--------|------|-----------------|
| 25101735 | Arshad Sheik | ArshadSheik  |
| 25003723 | CongYuan     | ycong1129    |
| 24679419 | Dong Bo      | DONG-BO-ERIC |
| 24194729 | Yitian Kong  | TomKongYT    |

---

## 📁 Project Structure

```
idea-incubator-hub/
│
├── app.py
├── requirements.txt
├── README.md
│
├── /templates          # HTML pages (Jinja2)
│   ├── base.html
│   ├── login.html
│   ├── signup.html
│   ├── home.html
│   ├── idea_detail.html
│   ├── submit_idea.html
│   ├── edit_idea.html
│   ├── profile.html
│   ├── my_ideas.html
│   ├── search_results.html
│   └── collaboration.html
│
├── /assets             # CSS, JS, Images
│   ├── /css
│   ├── /js
│   └── /images
│
|├── /checkpoint-meetings   # Lab checkpoint meeting discussion plans
│   ├── checkpoint-application-plan.md
|
├── /models             # SQLAlchemy database models
├── /routes             # Flask route blueprints
└── /instance           # SQLite database (auto-generated)
```

---

*CSS Framework: **Bootstrap***
