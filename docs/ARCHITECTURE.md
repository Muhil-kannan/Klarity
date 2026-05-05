# Architecture

A technical overview of how Klarity is built and why.

---

## Overview

Klarity is a GitHub App — not a GitHub Action. This distinction matters:

- **GitHub Actions** run inside the contributor's PR context, which limits what they can do and requires the repo to opt-in per workflow file
- **GitHub Apps** are installed once at the repo or org level, receive webhooks for all events, and act with their own identity and permissions

Klarity receives webhook events from GitHub, processes them asynchronously in the background, and calls the GitHub API to post results.

---

## Request Flow

```
1. Contributor opens a PR on GitHub

2. GitHub fires a POST request to Klarity's /api/v1/webhook endpoint
   - Includes X-Hub-Signature-256 header for verification
   - Klarity returns HTTP 200 immediately (no blocking)

3. The event is placed in the Redis job queue (ARQ)

4. A background worker picks up the job and runs the analysis pipeline:
   a. Fetch PR details, files, and commits from GitHub API
   b. Fetch .klarity.yml config from the repo (falls back to defaults)
   c. Run heuristic checks (6 factors → 0–100 score)
   d. Run AI slop signal detection
   e. Look up contributor's merged PR count

5. Score calculated with breakdown

6. Klarity calls GitHub API to:
   - Post a score comment on the PR
   - Apply labels (suspected-ai, needs-tests, etc.)

7. Score saved to SQLite database

8. Dashboard reflects the new score
```

---

## Components

### Backend (FastAPI)

The backend is a Python 3.12 FastAPI application with two entry points:

- **Web server** (`uvicorn app.main:app`) — handles incoming webhooks and serves the dashboard API
- **Worker** (`python -m app.jobs.worker`) — processes background jobs from the Redis queue

They share the same codebase and database but run as separate processes (separate containers in Docker Compose).

**Why separate processes?**
Webhook handlers must return HTTP 200 within a few seconds or GitHub will retry. Scoring can take longer (especially with LLM analysis in v0.2). Decoupling via a job queue means the webhook handler is always fast.

### Scoring Engine

Located in `backend/app/scoring/`.

The engine runs two parallel analyses:

1. **Heuristic checks** (`heuristics.py`) — deterministic, rule-based, fast. Each check returns a score and an optional suggestion. Weights are configurable via `.klarity.yml`.

2. **Slop detector** (`slop_detector.py`) — aggregates weighted signals to determine if a PR shows AI generation patterns. Returns a boolean + list of triggered signals.

The engine is designed to be extended — adding a new check is a matter of adding a function and registering it in `run_all_checks()`.

### GitHub Client

Located in `backend/app/github/`.

All GitHub API calls go through `GitHubClient`. It handles:
- JWT generation for GitHub App authentication
- Installation token exchange (tokens are valid for 1 hour)
- Pagination for PR files and commits
- Label creation (idempotent — won't fail if label already exists)

### Job Queue

Redis + ARQ. ARQ is a lightweight async job queue built on Redis. Jobs are serialized as JSON and processed by the worker.

The worker runs with `max_jobs=10` and a 120-second timeout per job. Failed jobs are logged with full error context.

### Database

SQLite by default (zero config), PostgreSQL for production deployments.

Models:
- `PRScore` — stores the score and breakdown for each analyzed PR
- `WebhookEvent` — audit log of all received webhook events
- `ContributorReputation` — per-repo contributor history (populated in v0.2)
- `Repository` — tracks installed repos and their installation IDs

### Dashboard (Next.js 16.2)

A server-rendered Next.js app using the App Router. Pages that need data fetch it server-side from the backend API.

Authentication is handled by NextAuth.js with the GitHub OAuth provider. Only users who are collaborators of the installed repo can access its dashboard (enforced by the backend API in v0.3).

The dashboard proxies API calls to the backend via Next.js rewrites — the frontend never calls the backend directly from the browser in production.

---

## Security

**Webhook signature verification:**
Every incoming webhook is verified using HMAC-SHA256 with the webhook secret. Requests with missing or invalid signatures are rejected with HTTP 401 before any processing occurs.

**GitHub App private key:**
The private key is stored as an environment variable (never committed). It's used to generate short-lived JWTs (9-minute expiry) which are exchanged for installation tokens.

**No external API calls:**
All analysis runs locally. PR content is never sent to external services. The only outbound calls are to `api.github.com`.

**Non-root Docker containers:**
Both the backend and dashboard containers run as non-root users.

---

## Configuration

Per-repo configuration is loaded from `.klarity.yml` in the repository root. Klarity fetches this file via the GitHub API on each analysis run.

If the file doesn't exist or is invalid, Klarity falls back to sensible defaults — it never crashes on bad config.

---

## Extending Klarity

### Adding a new heuristic check

1. Add a function to `backend/app/scoring/heuristics.py`:

```python
def check_my_new_thing(pr_body: str, weights: HeuristicWeights) -> CheckResult:
    # your logic here
    return CheckResult(score=..., max_score=..., passed=..., suggestion=...)
```

2. Register it in `run_all_checks()`:

```python
checks = {
    ...
    "my_new_thing": check_my_new_thing(pr_body, weights),
}
```

3. Add the weight to `HeuristicWeights` and `ScoringConfig`.

### Adding a new slop signal

Add a new `SlopSignal` to the `signals` list in `detect_slop()` in `slop_detector.py`. Set the weight to `"high"`, `"medium"`, or `"low"`.

---

## Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| Backend language | Python 3.12 | Best AI/ML ecosystem, fast to prototype |
| Web framework | FastAPI | Async, auto-docs, great DX |
| Job queue | Redis + ARQ | Lightweight async jobs, webhook decoupling |
| ORM | SQLModel | Type-safe, works with SQLite and PostgreSQL |
| GitHub SDK | httpx + PyJWT | Direct API calls, full control |
| Frontend | Next.js 16.2 | App Router, server components, great DX |
| Styling | Tailwind CSS | Fast, consistent, dark mode first |
| Auth | NextAuth.js | GitHub OAuth, zero friction |
| Containers | Docker Compose | One command to run everything |
