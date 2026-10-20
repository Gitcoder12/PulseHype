"""
PulseHype Backend v1.3
- Hacker News for Tech / All / Science
- RSS (feedparser) for World, Gaming, Movies, Funny
- No Reddit
"""

from __future__ import annotations

import os
import time
import hashlib
from typing import Any, Dict, List, Optional
from email.utils import parsedate_to_datetime

import requests
import feedparser
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(__name__, static_folder=ROOT, static_url_path="")
CORS(app)

CACHE_TTL = 60
_cache: Dict[str, tuple] = {}

# Feed sources
HN_FEEDS = {"all", "technology", "hackernews", "science", "programming"}
RSS_FEEDS = {
    "worldnews": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    ],
    "gaming": [
        "https://www.ign.com/rss/articles/feed",
        "https://www.pcgamer.com/rss/",
    ],
    "movies": [
        "https://variety.com/feed/",
        "https://www.hollywoodreporter.com/feed/",
    ],
    "funny": [
        "https://www.reddit.com/r/funny/.rss",  # last resort, may fail
        "https://feeds.theonion.com/onion/daily",
    ],
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
    "epic", "legend", "goat", "ai", "openai",
}
NEGATIVE = {
    "hate", "terrible", "awful", "worst", "broken", "failed", "dead",
    "crisis", "disaster", "banned", "scam", "fraud", "attack", "kill",
    "death", "war", "crash", "toxic", "horrible", "outrage", "shocking",
    "exposed", "scandal", "layoff",
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
    return min(99, max(5, round(velocity / 8)))


def enrich(post: Dict) -> Dict:
    return {
        "id": post.get("id"),
        "title": post.get("title"),
        "subreddit": post.get("subreddit", "news"),
        "author": post.get("author", "unknown"),
        "ups": post.get("ups", 0),
        "num_comments": post.get("num_comments", 0),
        "upvote_ratio": post.get("upvote_ratio", 0.9),
        "created_utc": post.get("created_utc", time.time()),
        "permalink": post.get("permalink") or post.get("url"),
        "url": post.get("url"),
        "over_18": False,
        "link_flair_text": None,
        "hype": hype_score(post),
        "sentiment": sentiment(post.get("title", "")),
        "source": post.get("source", "rss"),
    }


# ---------- Hacker News ----------
def fetch_hn(limit: int = 40) -> List[Dict]:
    try:
        print("[HN] Fetching topstories.json ...")
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10,
        ).json()[:limit]

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
                    "id": str(item["id"]),
                    "title": item["title"],
                    "subreddit": "hackernews",
                    "author": item.get("by", "unknown"),
                    "ups": item.get("score", 0) or 0,
                    "num_comments": item.get("descendants", 0) or 0,
                    "created_utc": item.get("time", time.time()),
                    "permalink": f"https://news.ycombinator.com/item?id={item['id']}",
                    "url": item.get("url") or f"https://news.ycombinator.com/item?id={item['id']}",
                    "source": "hackernews",
                })
            except Exception as e:
                print(f"[HN] item {story_id} failed: {e}")
                continue

        print(f"Fetched {len(posts)} HN posts")
        return posts
    except Exception as e:
        print(f"[HN] FATAL: {e}")
        return []


# ---------- RSS via feedparser ----------
def _parse_date(entry) -> float:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return time.mktime(t)
            except Exception:
                pass
    return time.time()


def fetch_rss(urls: List[str], label: str, limit: int = 30) -> List[Dict]:
    posts = []
    for url in urls:
        try:
            print(f"[RSS] Fetching {url}")
            feed = feedparser.parse(url)
            if not feed.entries:
                print(f"[RSS] No entries from {url}")
                continue
            for entry in feed.entries[:limit]:
                title = entry.get("title", "").strip()
                if not title:
                    continue
                link = entry.get("link", "")
                uid = entry.get("id") or entry.get("guid") or link or title
                pid = hashlib.md5(str(uid).encode()).hexdigest()[:12]
                posts.append({
                    "id": pid,
                    "title": title,
                    "subreddit": label,
                    "author": entry.get("author", label),
                    "ups": 50 + (hash(title) % 200),  # synthetic engagement for ranking
                    "num_comments": 5 + (hash(title) % 40),
                    "created_utc": _parse_date(entry),
                    "permalink": link,
                    "url": link,
                    "source": "rss",
                })
            print(f"[RSS] Got {len(feed.entries)} entries from {url}")
        except Exception as e:
            print(f"[RSS] Failed {url}: {e}")
            continue
    return posts


# ---------- Routes ----------
@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "PulseHype",
        "version": "1.3.0",
        "sources": ["hackernews", "rss"],
    })


@app.route("/api/feeds")
def list_feeds():
    return jsonify({"feeds": ["all", "technology", "hackernews", "worldnews", "gaming", "movies", "science", "funny"]})


@app.route("/api/feed/<feed_name>")
def get_feed(feed_name: str):
    cache_key = f"feed:{feed_name}"
    cached = _get_cached(cache_key)
    if cached is not None:
        print(f"[CACHE] {feed_name} → {len(cached)} posts")
        return jsonify({"feed": feed_name, "cached": True, "posts": cached, "count": len(cached)})

    raw: List[Dict] = []

    if feed_name in HN_FEEDS or feed_name == "all":
        raw.extend(fetch_hn(40 if feed_name == "all" else 30))

    if feed_name in RSS_FEEDS:
        raw.extend(fetch_rss(RSS_FEEDS[feed_name], feed_name, limit=25))

    if feed_name == "all":
        # Mix a bit of world + gaming for variety
        raw.extend(fetch_rss(RSS_FEEDS["worldnews"], "worldnews", limit=10))
        raw.extend(fetch_rss(RSS_FEEDS["gaming"], "gaming", limit=8))

    if not raw:
        print(f"[WARN] No posts for feed={feed_name}")
        return jsonify({"feed": feed_name, "cached": False, "posts": [], "count": 0})

    # Deduplicate by id
    seen = set()
    unique = []
    for p in raw:
        pid = p.get("id")
        if pid and pid not in seen:
            seen.add(pid)
            unique.append(enrich(p))

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

    raw = fetch_hn(25)
    unique = [enrich(p) for p in raw]
    unique.sort(key=lambda x: x["hype"], reverse=True)
    top = unique[:15]
    _set_cache(cache_key, top)
    print(f"[API] /api/trending → {len(top)} posts")
    return jsonify({"posts": top})


if __name__ == "__main__":
    print("=" * 55)
    print("PulseHype v1.3  |  HN + RSS (no Reddit)")
    print("http://localhost:5000")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=True)
