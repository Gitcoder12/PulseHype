"""
PulseHype Backend
-----------------
Lightweight Flask API that:
1. Serves the existing frontend
2. Proxies Reddit feeds (avoids CORS issues)
3. Adds server-side hype scoring + simple caching
4. Exposes clean JSON endpoints
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

# Resolve project root (one level up from this file)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

app = Flask(__name__, static_folder=ROOT, static_url_path="")
CORS(app)

REDDIT_USER_AGENT = "PulseHype/1.0 (by /u/Gitcoder12)"
CACHE_TTL = 45
FEEDS = {
    "all": ["all"],
    "technology": ["technology", "programming"],
    "worldnews": ["worldnews", "news"],
    "gaming": ["gaming", "pcgaming"],
    "science": ["science", "space"],
    "movies": ["movies", "television"],
    "funny": ["funny", "memes"],
}

_cache: Dict[str, tuple] = {}


def _get_cached(key: str) -> Optional[Any]:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None


def _set_cache(key: str, data: Any) -> None:
    _cache[key] = (time.time(), data)


POSITIVE = {
    "amazing", "incredible", "love", "great", "awesome", "best", "happy",
    "wonderful", "fantastic", "excellent", "brilliant", "perfect", "success",
    "win", "breakthrough", "revolutionary", "solved", "fixed", "beautiful",
    "epic", "legend", "goat",
}
NEGATIVE = {
    "hate", "terrible", "awful", "worst", "broken", "failed", "dead",
    "crisis", "disaster", "banned", "scam", "fraud", "attack", "kill",
    "death", "war", "crash", "toxic", "disgusting", "horrible", "outrage",
    "shocking", "exposed", "scandal",
}
HYPE = {
    "viral", "breaking", "leaked", "exclusive", "finally", "confirmed",
    "official", "huge", "massive", "major", "historic", "just", "now",
}


def sentiment(title: str) -> Dict[str, Any]:
    lower = title.lower()
    pos = sum(1 for w in POSITIVE if w in lower)
    neg = sum(1 for w in NEGATIVE if w in lower)
    hype = sum(1 for w in HYPE if w in lower)
    if pos > neg:
        return {"label": "positive", "icon": "🟢", "score": pos}
    if neg > pos:
        return {"label": "negative", "icon": "🔴", "score": neg}
    if hype > 0:
        return {"label": "mixed", "icon": "🟡", "score": hype}
    return {"label": "neutral", "icon": "🔵", "score": 0}


def hype_score(post: Dict) -> int:
    ups = post.get("ups", 0) or 0
    comments = post.get("num_comments", 0) or 0
    ratio = post.get("upvote_ratio", 0.5) or 0.5
    created = post.get("created_utc", time.time())
    hour_age = max(1.0, (time.time() - created) / 3600.0)
    velocity = (ups + comments * 3) / ((hour_age + 2) ** 1.5)
    controversy = 1.4 if ratio < 0.6 else 1.0
    return min(99, round(velocity * controversy / 10))


def fetch_subreddit(sub: str, limit: int = 25) -> List[Dict]:
    url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
    headers = {"User-Agent": REDDIT_USER_AGENT}
    try:
        r = requests.get(url, headers=headers, timeout=8)
        r.raise_for_status()
        return [c["data"] for c in r.json()["data"]["children"]]
    except Exception as e:
        app.logger.warning(f"Failed to fetch r/{sub}: {e}")
        return []


def enrich(post: Dict) -> Dict:
    return {
        "id": post.get("id"),
        "title": post.get("title"),
        "subreddit": post.get("subreddit"),
        "author": post.get("author"),
        "ups": post.get("ups", 0),
        "num_comments": post.get("num_comments", 0),
        "upvote_ratio": post.get("upvote_ratio", 0.5),
        "created_utc": post.get("created_utc"),
        "permalink": post.get("permalink"),
        "url": post.get("url"),
        "over_18": post.get("over_18", False),
        "link_flair_text": post.get("link_flair_text"),
        "hype": hype_score(post),
        "sentiment": sentiment(post.get("title", "")),
    }


@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "PulseHype", "version": "1.0.0"})


@app.route("/api/feeds")
def list_feeds():
    return jsonify({"feeds": list(FEEDS.keys())})


@app.route("/api/feed/<feed_name>")
def get_feed(feed_name: str):
    if feed_name not in FEEDS:
        return jsonify({"error": "unknown feed"}), 404

    cache_key = f"feed:{feed_name}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return jsonify({"feed": feed_name, "cached": True, "posts": cached})

    all_posts = []
    for sub in FEEDS[feed_name]:
        all_posts.extend(fetch_subreddit(sub))

    seen = set()
    unique = []
    for p in all_posts:
        pid = p.get("id")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(enrich(p))

    unique.sort(key=lambda x: x["hype"], reverse=True)
    _set_cache(cache_key, unique)
    return jsonify({"feed": feed_name, "cached": False, "posts": unique})


@app.route("/api/trending")
def trending():
    cache_key = "trending"
    cached = _get_cached(cache_key)
    if cached is not None:
        return jsonify({"posts": cached})

    all_posts = []
    for feed in FEEDS:
        for sub in FEEDS[feed]:
            all_posts.extend(fetch_subreddit(sub, limit=10))

    seen = set()
    unique = []
    for p in all_posts:
        pid = p.get("id")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(enrich(p))

    unique.sort(key=lambda x: x["hype"], reverse=True)
    top = unique[:15]
    _set_cache(cache_key, top)
    return jsonify({"posts": top})


if __name__ == "__main__":
    print("PulseHype running → http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
