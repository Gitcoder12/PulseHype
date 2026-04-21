# PulseHype 🔥

> Real-time viral content aggregator. Uses sentiment analysis to filter out the noise and show only what's actually blowing up across the internet, all in one place.

---

## What is PulseHype?

PulseHype cuts through the endless scroll of regular news and feeds to show you **only what's going viral — right now**. Powered by Real-Time Sentiment Analysis (RTSA), it scores content across platforms by engagement velocity, emotional reaction intensity, and cross-platform spread.

No editorial bias. No noise. Just the pulse of the internet.

---

## Features

- **RTSA Engine** — Real-Time Sentiment Analysis scores content as it spreads
- **Cross-platform aggregation** — pulls viral signals from multiple sources in one place
- **Viral-only filter** — regular news and low-engagement content are automatically excluded
- **Live dashboard** — content ranked and updated in real time
- **Trend velocity tracking** — see what's rising fast, not just what's already peaked

---

## Tech Stack

| Layer     | Technology              |
|-----------|-------------------------|
| Frontend  | React                   |
| Backend   | Flask (Python)          |
| Database  | SQLite                  |
| Analysis  | RTSA / Sentiment scoring |
| APIs      | Aggregated content feeds |

---

## Getting Started

```bash
# Clone the repo
git clone https://github.com/Gitcoder12/PulseHype.git
cd PulseHype

# Backend
pip install -r requirements.txt
python app.py

# Frontend
cd client
npm install
npm start
```

---

## Project Structure

```
PulseHype/
├── app.py              # Flask backend
├── rtsa/               # Sentiment analysis engine
├── client/             # React frontend
│   ├── src/
│   │   ├── components/
│   │   └── pages/
├── requirements.txt
└── README.md
```

---

## How RTSA Works

1. Content is pulled from aggregated sources continuously
2. Each piece is scored on **sentiment intensity**, **reaction speed**, and **spread breadth**
3. Only content crossing the viral threshold is surfaced
4. Scores update in real time as engagement grows or drops

---

## Author

**Dharavath Satvik** — M.Tech CSE, Amity University Hyderabad  
GitHub: [@Gitcoder12](https://github.com/Gitcoder12)

---

## License

MIT
