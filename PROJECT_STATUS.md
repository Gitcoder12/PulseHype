# Project Status — PulseHype

**Snapshot date:** 2026-11-16  
**Status type:** Initial documentation and repository-tree assessment  
**Default branch:** main  
**Review completeness:** Partial — not a code audit or release certification

## Project purpose
Flask dashboard for aggregating Reddit posts and ranking them with a transparent engagement-velocity/controversy score.

## Current maturity (README-declared or visible scaffolding; not independently verified)
Root includes backend/, frontend/, index.html and requirements.txt. README describes Reddit public JSON API ingestion, sentiment keywords and a 45-second in-memory cache.

## Observed repository structure
.env.example, backend/, frontend/, index.html, requirements.txt, README.md and project governance files.

## Known issues and risks to investigate
README's 'real-time' wording and Hype Score are product claims, not validated predictive measures. No automated tests/CI were visible in the observed root. Verify Reddit endpoint availability/rate-limit behavior, parsing failures, timezone/age math, caching and safe HTML rendering. Engagement score should not be described as a validated virality predictor without evaluation.

## Recommended next actions
Inspect API clients and score implementation; add fixtures for missing/removed posts and rate limiting; test cache expiration and score formula; identify source/time for each item; escape untrusted post content; describe Hype Score as a heuristic ranking unless empirically validated.

## Verification record
| Check | Result |
|---|---|
| Default-branch top-level tree | Inspected |
| README | Inspected |
| Deep source review | Not performed |
| Tests / build / runtime | Not run |
| Security / dependency audit | Not run |
| Live deployment / API checks | Not run |
| Independent review | Not performed |

## Change log
- 2026-11-16: Added this initial status snapshot on a review branch. No application code or existing data changed.

> Update this file only after the corresponding inspection or verification has actually been performed. Distinguish observed facts, README claims, hypotheses and unrun checks.