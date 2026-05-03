"""
services/news_service.py
Fetches recent news articles per idea category from NewsAPI.
Results cached in market_trends table for 24 hours.
Sign up free at https://newsapi.org — add NEWS_API_KEY to .env
"""

import json, os, requests
from datetime import datetime, timedelta
from models.models import db, MarketTrend

NEWSAPI_URL = "https://newsapi.org/v2/everything"

CATEGORY_KEYWORDS = {
    "FinTech":         "fintech startup finance app",
    "EdTech":          "edtech education technology startup",
    "GreenTech":       "greentech climate sustainability startup",
    "Health":          "healthtech digital health startup",
    "DevTools":        "developer tools software startup",
    "Productivity":    "productivity app startup",
    "Social":          "social media startup platform",
    "Creator Economy": "creator economy content monetisation",
    "Other":           "startup innovation",
}


def get_news_for_category(category: str, max_articles: int = 5) -> list:
    cached = MarketTrend.query.filter_by(
        category=category, source="newsapi"
    ).order_by(MarketTrend.fetched_at.desc()).first()

    if cached and not cached.is_stale():
        return cached.data()[:max_articles]

    articles = _fetch(category, max_articles)

    if cached:
        cached.data_json  = json.dumps(articles)
        cached.fetched_at = datetime.utcnow()
    else:
        db.session.add(MarketTrend(
            category=category, source="newsapi",
            data_json=json.dumps(articles),
        ))
    db.session.commit()
    return articles


def _fetch(category: str, n: int) -> list:
    api_key = os.getenv("NEWS_API_KEY", "")
    if not api_key:
        return []
    keyword = CATEGORY_KEYWORDS.get(category, "startup")
    try:
        r = requests.get(NEWSAPI_URL, params={
            "q": keyword, "sortBy": "publishedAt",
            "pageSize": n, "language": "en", "apiKey": api_key,
        }, timeout=10)
        r.raise_for_status()
        return [
            {
                "title":        a.get("title", ""),
                "source":       a.get("source", {}).get("name", ""),
                "url":          a.get("url", ""),
                "published_at": a.get("publishedAt", ""),
                "description":  a.get("description", ""),
                "image":        a.get("urlToImage", ""),
            }
            for a in r.json().get("articles", [])
        ]
    except Exception:
        return []