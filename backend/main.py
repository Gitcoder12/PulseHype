"""
PulseHype Backend v1.2
100% Hacker News – Reddit removed (blocked)
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

CACHE_TTL = 45
_cache: Dict[str, tuple] = {}

FEEDS = {
    "all": "top",
    "technology": "top",
    "worldnews": "top",
    "gaming": "top",
    "science": "top",
    "movies": "top",
    "funny": "top",
    "hackernews": "top",
    "new": "new",
    "best": "best",
}


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
    "epic", "legend", "goat", "ai", "openai", "llm",
}
NEGATIVE = {
    "hate", "terrible", "awful", "worst", "broken", "failed", "dead",
    "crisis", "disaster", "banned", "scam", "fraud", "attack", "kill",
    "death", "war", "crash", "toxic", "disgusting", "horrible", "outrage",
    "shocking", "exposed", "scandal", "layoff",
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
    created = post.get("created_utc", time.time())
    hour_age = max(1.0, (time.time() - created) / 3600.0)
    velocity = (ups + comments * 3) / ((hour_age + 2) ** 1.5)
    return min(99, round(velocity / 8))


def enrich(post: Dict) -> Dict:
    return {
        "id": post.get("id"),
        "title": post.get("title"),
        "subreddit": post.get("subreddit", "hackernews"),
        "author": post.get("author"),
        "ups": post.get("ups", 0),
        "num_comments": post.get("num_comments", 0),
        "upvote_ratio": 0.9,
        "created_utc": post.get("created_utc"),
        "permalink": post.get("permalink"),
        "url": post.get("url"),
        "over_18": False,
        "link_flair_text": None,
        "hype": hype_score(post),
        "sentiment": sentiment(post.get("title", "")),
        "source": "hackernews",
    }


# ---------- Hacker News only ----------
def fetch_hn(story_type: str = "top", limit: int = 40) -> List[Dict]:
    """
    story_type: top | new | best
    """
    endpoint = {
        "top": "topstories",
        "new": "newstories",
        "best": "beststories",
    }.get(story_type, "topstories")

    try:
        print(f"[HN] Fetching {endpoint}.json ...")
        ids = requests.get(
            f"https://hacker-news.firebaseio.com/v0/{endpoint}.json",
            timeout=10,
        ).json()

        if not ids:
            print("[HN] No story IDs returned")
            return []

        ids = ids[:limit]
        posts = []

        for story_id in ids:
            try:
                item = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                    timeout=5,
                ).json()
                if not item or item.get("type") != "story" or not item.get("title"):
                    continue

                posts.append({
                    "id": str(item.get("id")),
                    "title": item.get("title", ""),
                    "subreddit": "hackernews",
                    "author": item.get("by", "unknown"),
                    "ups": item.get("score", 0) or 0,
                    "num_comments": item.get("descendants", 0) or 0,
                    "created_utc": item.get("time", time.time()),
                    "permalink": f"https://news.ycombinator.com/item?id={item.get('id')}",
                    "url": item.get("url") or f"https://news.ycombinator.com/item?id={item.get('id')}",
                })
            except Exception as e:
                print(f"[HN] item {story_id} failed: {e}")
                continue

        print(f"Fetched {len(posts)} HN posts")
        return posts

    except Exception as e:
        print(f"[HN] FATAL fetch error: {e}")
        return []


# ---------- Routes ----------
@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "PulseHype", "version": "1.2.0", "source": "hackernews"})


@app.route("/api/feeds")
def list_feeds():
    return jsonify({"feeds": list(FEEDS.keys())})


@app.route("/api/feed/<feed_name>")
def get_feed(feed_name: str):
    cache_key = f"feed:{feed_name}"
    cached = _get_cached(cache_key)
    if cached is not None:
        print(f"[CACHE] hit for {feed_name} ({len(cached)} posts)")
        return jsonify({"feed": feed_name, "cached": True, "posts": cached, "count": len(cached)})

    story_type = FEEDS.get(feed_name, "top")
    raw = fetch_hn(story_type, limit=40)

    unique = [enrich(p) for p in raw]
    unique.sort(key=lambda x: x["hype"], reverse=True)

    _set_cache(cache_key, unique)
    print(f"[API] /api/feed/{feed_name} → {len(unique)} posts")
    return jsonify({"feed": feed_name, "cached": False, "posts": unique, "count": len(unique)})


@app.route("/api/trending")
def trending():
    cache_key = "trending"
    cached = _get_cached(cache_key)
    if cached is not None:
        return jsonify({"posts": cached})

    raw = fetch_hn("top", limit=25)
    unique = [enrich(p) for p in raw]
    unique.sort(key=lambda x: x["hype"], reverse=True)
    top = unique[:15]
    _set_cache(cache_key, top)
    print(f"[API] /api/trending → {len(top)} posts")
    return jsonify({"posts": top})


if __name__ == "__main__":
    print("=" * 50)
    print("PulseHype v1.2  |  100% Hacker News")
    print("http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
