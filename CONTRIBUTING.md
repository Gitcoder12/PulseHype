# Contributing to PulseHype

## Adding a New Data Source
1. Create `sources/your_platform.js`
2. Export a `fetchViral()` function returning items scored 0–100
3. Register in the main aggregator

## Viral Score Formula
`score = (engagement_velocity * 0.5) + (sentiment_intensity * 0.3) + (cross_platform_spread * 0.2)`
