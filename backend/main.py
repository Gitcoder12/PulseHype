"""
PulseHype Backend v1.1
- Robust Reddit fetching with proper headers
- Hacker News as live fallback / extra source
- In-memory cache
- Serves the frontend
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(__name__, static_folder=ROOT, static_url_path="")
CORS(app)

# ---------- Config ----------
CACHE_TTL = 60
REDDIT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PulseHype/1.1; +https://github.com/Gitcoder12/PulseHype)",
    "Accept": "application/json",
}
# Optional privacy frontends (tried in order if official Reddit fails)
REDLIB_INSTANCES = [
    "https://redlib.privacyredirect.com",
    "https://libreddit.projectsegfau.lt",
    "https://reddit.rdt.workers.dev",
]

FEEDS = {
    "all": ["all"],
    "technology": ["technology", "programming", "MachineLearning"],
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


# ---------- Scoring ----------
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
    lower = (title or "").lower()
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
        "source": post.get("source", "reddit"),
    }


# ---------- Reddit fetch (with fallbacks) ----------
def fetch_reddit_official(sub: str, limit: int = 25) -> List[Dict]:
    url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
    try:
        r = requests.get(url, headers=REDDIT_HEADERS, timeout=10)
        if r.status_code == 200:
            children = r.json().get("data", {}).get("children", [])
            return [c["data"] for c in children]
        app.logger.warning(f"Reddit official {sub}: {r.status_code}")
    except Exception as e:
        app.logger.warning(f"Reddit official error {sub}: {e}")
    return []


def fetch_reddit_redlib(sub: str, limit: int = 25) -> List[Dict]:
    """Try privacy frontends that often still work when official Reddit blocks."""
    for base in REDLIB_INSTANCES:
        try:
            # Most redlib/libreddit instances expose /r/sub/hot.json or similar
            url = f"{base}/r/{sub}/hot.json?limit={limit}"
            r = requests.get(url, headers=REDDIT_HEADERS, timeout=8)
            if r.status_code == 200:
                data = r.json()
                children = data.get("data", {}).get("children", [])
                if children:
                    return [c["data"] for c in children]
        except Exception:
            continue
    return []


def fetch_subreddit(sub: str, limit: int = 25) -> List[Dict]:
    posts = fetch_reddit_official(sub, limit)
    if not posts:
        posts = fetch_reddit_redlib(sub, limit)
    for p in posts:
        p["source"] = "reddit"
    return posts


# ---------- Hacker News (always live & free) ----------
def fetch_hackernews(limit: int = 30) -> List[Dict]:
    """Convert HN top stories into the same shape we use for Reddit posts."""
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=8,
        ).json()[:limit]

        posts = []
        for i, story_id in enumerate(ids):
            try:
                item = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                    timeout=5,
                ).json()
                if not item or item.get("type") != "story":
                    continue
                # Map HN fields → our common shape
                posts.append({
                    "id": str(item.get("id")),
                    "title": item.get("title", ""),
                    "subreddit": "hackernews",
                    "author": item.get("by", "unknown"),
                    "ups": item.get("score", 0),
                    "num_comments": item.get("descendants", 0),
                    "upvote_ratio": 0.9,
                    "created_utc": item.get("time", time.time()),
                    "permalink": f"/item?id={item.get('id')}",
                    "url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}",
                    "over_18": False,
                    "link_flair_text": None,
                    "source": "hackernews",
                })
            except Exception:
                continue
            if len(posts) >= limit:
                break
        return posts
    except Exception as e:
        app.logger.warning(f"Hacker News fetch failed: {e}")
        return []


# ---------- Routes ----------
@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "PulseHype", "version": "1.1.0"})


@app.route("/api/feeds")
def list_feeds():
    return jsonify({"feeds": list(FEEDS.keys()) + ["hackernews"]})


@app.route("/api/feed/<feed_name>")
def get_feed(feed_name: str):
    cache_key = f"feed:{feed_name}"
    cached = _get_cached(cache_key)
    if cached is not None:
        return jsonify({"feed": feed_name, "cached": True, "posts": cached})

    all_posts: List[Dict] = []

    # Special feed: pure Hacker News
    if feed_name == "hackernews":
        all_posts = fetch_hackernews(40)
    else:
        # Reddit feeds
        subs = FEEDS.get(feed_name)
        if not subs:
            return jsonify({"error": "unknown feed"}), 404

        for sub in subs:
            all_posts.extend(fetch_subreddit(sub))

        # For technology / all also mix in some HN for reliability
        if feed_name in ("technology", "all") and len(all_posts) < 10:
            all_posts.extend(fetch_hackernews(20))

    # Deduplicate by id
    seen = set()
    unique = []
    for p in all_posts:
        pid = p.get("id")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(enrich(p))

    unique.sort(key=lambda x: x["hype"], reverse=True)
    _set_cache(cache_key, unique)
    return jsonify({"feed": feed_name, "cached": False, "posts": unique, "count": len(unique)})


@app.route("/api/trending")
def trending():
    cache_key = "trending"
    cached = _get_cached(cache_key)
    if cached is not None:
        return jsonify({"posts": cached})

    all_posts: List[Dict] = []
    # Mix Reddit + HN
    for sub in ["all", "technology", "worldnews"]:
        all_posts.extend(fetch_subreddit(sub, limit=15))
    all_posts.extend(fetch_hackernews(20))

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
    print("PulseHype v1.1 running → http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
