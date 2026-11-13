# PulseHype — Feature Upgrade Plan

## Objective

A dashboard that collects stories from Hacker News and selected RSS feeds, then sorts them using simple engagement and keyword signals.

## P0 — source correctness

- [ ] Remove obsolete Reddit placeholders and make configuration reflect actual provider adapters; issue #2 records this mismatch.
- [ ] Add feed provenance, publication/update timestamps, duplicate handling and safe parser error behavior.

## P1 — explainable reader experience

- [ ] Expose ranking components so users can inspect why a story was ordered highly.
- [ ] Add source filters, topic controls, accessibility and clear unavailable-source states.

## P2 — evaluation and reliability

- [ ] Evaluate ranking quality on a labelled set and compare with chronological/popularity baselines.
- [ ] Add bounded cache, rate-limit and feed freshness monitoring.

## Contributor work packages

1. Feed adapter and source schema.
2. Parsing, deduplication and failure handling.
3. Transparent ranking and user controls.
4. Reproducible ranking evaluation and freshness monitoring.

## Definition of done

- [ ] Every result shows its source and timestamp.
- [ ] Provider failures are isolated and visible.
- [ ] Ranking factors are inspectable and tested.
- [ ] README avoids claims of objective importance or representative sentiment.
