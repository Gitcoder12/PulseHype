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
