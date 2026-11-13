# PulseHype

**A real-time feed dashboard that ranks stories using a lightweight engagement and sentiment heuristic.**

[![License](https://img.shields.io/badge/license-see%20LICENSE-lightgrey)](LICENSE)

PulseHype collects items from Hacker News and configured RSS feeds, enriches them with simple keyword-based sentiment signals, and sorts them by a project-defined Hype score.

## Features

- Hacker News feeds for technology, science, and programming topics.
- RSS-based feeds for selected world-news, gaming, film, and entertainment sources.
- Heuristic engagement-velocity ranking.
- Keyword-based positive, negative, and hype signals.
- Short-lived in-memory cache to reduce repeated feed requests.
- Flask API with a static browser frontend.

## Quick Start

```bash
git clone https://github.com/Gitcoder12/PulseHype.git
cd PulseHype

python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS / Linux: source .venv/bin/activate

pip install -r requirements.txt
python backend/main.py
```

Open `http://localhost:5000`.

## Tech Stack

Python · Flask · Flask-CORS · Requests · Feedparser · HTML · CSS · JavaScript

## Project Structure

```text
PulseHype/
├── backend/     # Flask routes, feed retrieval, scoring, and caching
├── frontend/    # Browser interface components and assets
├── index.html   # Root browser entry page
└── requirements.txt
```

## Scope and Limitations

Hype and sentiment scores are transparent heuristics, not validated measures of virality, public opinion, or importance. RSS feeds and third-party services can change, rate-limit, or become unavailable. The current implementation does not use Reddit as a source.

## License

See [LICENSE](LICENSE).

---

## Project handbook

- [Activity log](ACTIVITY_LOG.md) · [Feature upgrade plan](FEATURE_UPGRADE_PLAN.md)
- [Company and team fit](COMPANY_FIT.md) · [README explanation draft](README_ADDENDUM_DRAFT.md)
- [README quality checklist](README_QUALITY_CHECKLIST.md)
- [Contributing](CONTRIBUTING.md) · [Agent instructions](AGENTS.md) · [Agent skills](SKILLS.md)
