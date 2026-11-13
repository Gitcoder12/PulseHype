# PulseHype — README Explanation Draft

## In plain language

A dashboard that collects stories from Hacker News and selected RSS feeds, then sorts them using simple engagement and keyword signals.

## How it works

The app reads story items from configured sources, normalises their basic information and sorts them using simple project-defined signals. The ranking is a browsing aid, not a factual or editorial verdict.

## Technical explanation

Flask backend and static browser frontend. Sources include Hacker News and configured RSS feeds. Ranking uses a project-defined engagement-velocity heuristic and keyword-based sentiment/hype signals; it is not a validated measure of news importance or public opinion.

Document provider adapters, cache policy, item schema, score formula, tie-breaking, parser errors and frontend/API flow. Include an example result with the contributing score components.

## Limitations

Feeds may be delayed, unavailable or duplicated. Keyword sentiment can misread sarcasm, context, language and named entities. A high score does not mean a story is important or verified.

## Contributing

See FEATURE_UPGRADE_PLAN.md, CONTRIBUTING.md and ACTIVITY_LOG.md.
