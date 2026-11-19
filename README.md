# PulseHype 🔥

**Real-time viral content radar.**  
Cuts through the noise and shows only what’s actually blowing up right now — ranked by engagement velocity + sentiment intensity.

## Live Demo (local)

```bash
git clone https://github.com/Gitcoder12/PulseHype.git
cd PulseHype
pip install -r requirements.txt
python backend/main.py
```

Then open → **http://localhost:5000**

## What it does

- Pulls live hot posts from multiple Reddit communities
- Scores every post with a **Hype Score** (0-99) based on:
  - Upvotes + comment velocity
  - Age of the post (newer = higher potential)
  - Controversy boost (low upvote ratio)
- Runs lightweight keyword sentiment analysis
- Clean, dark, real-time dashboard

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Frontend dashboard |
| `GET /api/health` | Health check |
| `GET /api/feeds` | List available feeds |
| `GET /api/feed/<name>` | Posts for a feed (all, technology, gaming…) |
| `GET /api/trending` | Top 15 highest-hype posts across all feeds |

Example:
```bash
curl http://localhost:5000/api/feed/technology
curl http://localhost:5000/api/trending
```

## Architecture

```
PulseHype/
├── index.html          # Beautiful single-page frontend
├── backend/
│   └── main.py         # Flask API + scoring + caching
├── requirements.txt
└── README.md
```

### Why this design?

- Frontend stays pure HTML/JS → zero build step
- Backend only proxies Reddit + adds scoring → solves CORS and adds real value
- 45-second in-memory cache → polite to Reddit + fast responses
- Hype formula is transparent and easy to tune

## Hype Score formula (interview-ready)

```
velocity = (ups + comments × 3) / (age_hours + 2)^1.5
controversy = 1.4 if upvote_ratio < 0.6 else 1.0
hype = min(99, round(velocity × controversy / 10))
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Vanilla HTML/CSS/JS |
| Backend | Flask + flask-cors + requests |
| Data source | Reddit public JSON API |
| Caching | Simple in-memory TTL cache |

## License

MIT

---

**Author**: Dharavath Satvik ([@Gitcoder12](https://github.com/Gitcoder12))


---

## AI-maintained project notes (secondary — 2026-11-13)

This section supplements the maintainer-authored README above. The original text has been restored verbatim from Git-history baseline `77f71ce54a30eb6cf03a1e16c2068652a959b88d`; this addendum does not replace or certify the original claims.

- The current source tree, runtime data and tests are the implementation source of truth. Roadmap items, draft PRs and AI-generated descriptions are not shipped features by themselves.
- Preserve real and maintainer-provided data. Never silently substitute generated or placeholder data. Clearly label and isolate synthetic fixtures.
- Mark unverified sources, identifiers, metrics, benchmark results and external claims as unknown/unverified rather than guessing.
- Verify setup, execution, tests and public claims against the exact current commit before using this repository in a job, research or academic application.
- See [MODEL_AUDIT_ROUTER.md](MODEL_AUDIT_ROUTER.md) for independent model review instructions and the merge gate.

---

## Engineering Audit & Handover — 2026-11-17

**Reviewed commit:** `9f17f2d2a0ce8a3f698343b57271593f4b86c509` (`main`). Static inspection covered `backend/main.py` and the current README.

### Confirmed findings
- The README describes Reddit as the primary live source, but the inspected backend identifies its current sources as Hacker News and RSS; the health endpoint returns `hackernews` and `rss`.
- For RSS records, `fetch_rss()` fabricates `ups` and `num_comments` from Python's process-randomized `hash(title)`. Those values are not actual engagement counts, yet they feed the displayed hype score. Do not present RSS hype scores as measured engagement velocity.
- Sentiment is a keyword-substring heuristic over titles, not a trained sentiment model.
- The current implementation uses a 60-second in-memory cache. Cache state is process-local and is lost on restart; multiple workers do not share it.

### Next actions
1. Correct the README/source labels so data sources and engagement metrics match the actual implementation.
2. For RSS, separate measured fields from synthetic ranking features; label estimates explicitly and never display synthetic values as votes/comments.
3. Add source timestamps, per-source error visibility, tests for feed parsing, and deterministic scoring tests.

**Verification status:** static source inspection only; live feed freshness, UI integration, and runtime behavior remain unverified.

---

## Examples Used
- Ranking fast-rising technology discussions
- Comparing engagement velocity across posts
- Detecting sentiment shifts in a trending topic


---

## Comparison with Existing Open-Source Projects

PulseHype is documented as a feed-ranking dashboard that combines source activity, recency and lightweight sentiment signals to surface fast-rising discussions. These projects provide adjacent social-listening and trend-monitoring references.

| Project / resource | Established focus | Relationship to PulseHype |
|---|---|---|
| [SocialMediaTracker Streamlit WebApp](https://github.com/lokesh-76/SocialMediaTracker-Streamlit-WebApp) | Social-media monitoring and analytics dashboard | A general social-media tracking reference; PulseHype's documented distinction is a feed-oriented ranking based on recency/engagement velocity rather than broad account analytics. |
| [Zeitbot](https://github.com/ShonMG/zeitbot) | Trend-oriented monitoring and signal aggregation | An adjacent trend-monitoring project; compare actual source coverage and ranking logic before asserting feature parity. |
| [Reddit API](https://www.reddit.com/dev/api/) | Platform endpoints and public listing data | PulseHype depends on upstream source data; Reddit's API is an input interface, not a competing dashboard product. |

### Where PulseHype is different
- **Velocity-first ranking:** the README describes a custom Hype Score that combines engagement signals with post age and a controversy adjustment.
- **Feed aggregation:** the intended dashboard presents multiple topic feeds through one interface.
- **Transparent formula:** the scoring expression is documented so users can inspect and tune its assumptions.

### Where established alternatives are stronger
Dedicated social-listening platforms may offer broader source coverage, historical analytics, account-level insights and more robust sentiment models. PulseHype's current engineering audit found a mismatch between README claims and backend sources, and identified synthetic RSS engagement fields. It must not display fabricated votes/comments as measured engagement or describe keyword matching as trained sentiment analysis.

### Evidence and limitations
Show the source and retrieval timestamp for every item, separate measured fields from estimates, and expose partial-feed failures. Validate ranking with a labelled dataset and user study before claiming that the score identifies virality. This is a documented-scope comparison, not a ranking-quality benchmark.
