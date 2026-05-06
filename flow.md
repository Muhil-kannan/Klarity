# Klarity — Implementation Flow

## Current State (What's Done)

Phase 1 (v0.1) backend is largely built:

- FastAPI app with lifespan, CORS, middleware
- Webhook receiver + HMAC-SHA256 signature verification
- GitHub App auth (JWT + installation tokens)
- Heuristic scoring engine (6 factors, 0–100)
- AI slop detector
- Background job queue (Redis + ARQ)
- GitHub API client (PR data, labels, comments)
- Score comment posted to PR
- SQLite DB with SQLModel (PRScore, WebhookEvent models)
- `.klarity.yml` config parser
- Dashboard API route (basic)
- Next.js dashboard shell (queue page, stats bar, filter bar, score badge)
- Docker Compose setup
- Unit tests for heuristics + slop detector

---

## What's Missing Right Now (Immediate Next Steps)

### 1. Backend — Missing Pieces

#### `triage/` module — not created yet
The plans call for it in v0.2 but the directory doesn't exist.

- `backend/app/triage/issue_triage.py` — classify issues (bug, feature-request, question, needs-more-info)
- `backend/app/triage/duplicate.py` — ChromaDB semantic duplicate detection
- `backend/app/triage/stale.py` — stale issue management + auto-comment

#### `reputation/` module — not created yet
- `backend/app/reputation/tracker.py` — per-repo contributor history (merged, abandoned, avg score)

#### `notifications/` module — not created yet
- `backend/app/notifications/email.py` — weekly digest email
- `backend/app/notifications/slack.py` — Slack webhook
- `backend/app/notifications/discord.py` — Discord webhook

#### Webhook handler — only handles `pull_request.opened`
- Needs to handle `issues.opened`, `issues.edited`, `pull_request.edited`, `pull_request.synchronize`

#### DB models — incomplete
- `ContributorReputation` model missing
- `Repository` model missing (tracks installed repos + installation IDs)
- Alembic migrations not set up

#### LLM scorer — not created yet
- `backend/app/scoring/llm_scorer.py` — Ollama integration for PR description quality

#### Dashboard API — stub only
- `/dashboard/queue` — needs real pagination, filtering, sorting
- `/dashboard/stats` — needs real aggregation queries
- `/dashboard/contributors` — not implemented
- `/dashboard/suspected-ai` — not implemented

### 2. Frontend — Missing Pieces

- `dashboard/app/(dashboard)/suspected-ai/page.tsx` — exists but likely stub
- `dashboard/app/(dashboard)/contributors/page.tsx` — exists but likely stub
- `dashboard/app/(dashboard)/settings/page.tsx` — exists but likely stub
- `dashboard/app/(dashboard)/stale/page.tsx` — **missing entirely**
- `dashboard/components/layout/Sidebar.tsx` — check if implemented
- `dashboard/components/layout/Header.tsx` — check if implemented
- `DigestPreview` component — not created yet
- SWR real-time polling not wired up

### 3. Infrastructure — Missing
- `nginx/nginx.conf` — not created
- `.github/workflows/ci.yml` — not created
- `.github/workflows/docker-publish.yml` — not created
- Integration tests (`backend/tests/integration/`) — not created

---

## Implementation Order (Prioritized)

### Step 1 — Complete v0.1 (Close the gaps)

These are blockers before v0.1 is truly shippable:

1. **Webhook handler** — add `pull_request.synchronize` and `pull_request.edited` event handling so re-scoring works when a PR is updated
2. **DB models** — add `ContributorReputation` and `Repository` models, set up Alembic
3. **Dashboard API** — implement real `/dashboard/queue` with pagination + filters, `/dashboard/stats`
4. **Frontend layout** — wire up Sidebar + Header, confirm auth flow works end-to-end
5. **CI workflow** — `.github/workflows/ci.yml` so tests run on every PR (dogfooding)
6. **README** — setup guide with ngrok instructions + GIF demo

### Step 2 — v0.2: AI + Issue Triage

1. **Ollama LLM scorer** — `llm_scorer.py`, integrate into `engine.py` as optional step
2. **Issue triage** — `triage/` module, wire into webhook handler for `issues.opened`
3. **Duplicate detection** — ChromaDB + nomic-embed-text via Ollama
4. **Contributor reputation** — `reputation/tracker.py`, populate on each PR event
5. **Stale management** — scheduled ARQ job (daily cron) to check stale issues
6. **First-time contributor welcome** — detect in `tasks.py`, post welcome comment

### Step 3 — v0.3: Dashboard + Digest

1. **Stale page** — `dashboard/app/(dashboard)/stale/page.tsx`
2. **Contributors page** — full reputation view with merge/abandon stats
3. **Suspected AI page** — bulk close UI
4. **Settings page** — form that reads/writes `.klarity.yml` via GitHub API
5. **Notifications** — `notifications/` module (email, Slack, Discord)
6. **Weekly digest** — scheduled ARQ job, `DigestPreview` component
7. **Multi-repo support** — `Repository` model + repo selector in dashboard

### Step 4 — v1.0: Production Hardening

1. **Nginx config** — `nginx/nginx.conf` reverse proxy
2. **PostgreSQL support** — env-driven DB URL switch
3. **Security audit** — token handling, rate limiting, webhook replay protection
4. **Performance test** — simulate 1,000 simultaneous webhook events
5. **GitHub Marketplace** — app manifest, listing copy, screenshots
6. **Docs site** — Docusaurus or similar

---

## Additions That Would Make Klarity Better

These aren't in the current plans but would meaningfully improve the product:

### High Value

| Addition | Why |
|---|---|
| **PR re-score on update** | When a contributor fixes issues and pushes new commits, the score should update and the comment should be edited (not a new comment). Already partially supported via `update_pr_comment` in the client. |
| **Score trend chart** | Show a repo's average PR quality over time in the dashboard. Recharts is already in the stack. |
| **Webhook replay protection** | Store delivery IDs and reject duplicates. Prevents double-scoring if GitHub retries. |
| **Rate limit handling** | GitHub API has rate limits. The client needs exponential backoff + retry logic. |
| **`.klarity.yml` validation** | When the config file is malformed, post a comment on the next PR explaining the issue instead of silently falling back to defaults. |
| **Ignore list** | Allow maintainers to whitelist bots or trusted contributors (e.g., `dependabot`, `renovate`) so they don't get scored. |

### Medium Value

| Addition | Why |
|---|---|
| **PR diff content analysis** | Currently only file names and sizes are checked. Analyzing actual diff content (via LLM) would catch copy-paste code, commented-out blocks, and debug statements. |
| **Issue template auto-generation** | If a repo has no issue template, Klarity could suggest one based on the types of issues it has seen. |
| **Contributor leaderboard** | Public-facing page showing top contributors by score — incentivizes quality. |
| **Webhook delivery log in dashboard** | Show recent webhook events and their processing status. Useful for debugging. |
| **Dark/light mode toggle** | Plans mention dark mode by default but a toggle should be in the UI. |
| **Keyboard shortcuts** | j/k navigation, `c` to close, `s` to snooze — mentioned in plans but not implemented. |

### Future / Post v1.0

| Addition | Why |
|---|---|
| **GitHub Actions mode** | Some maintainers prefer Actions over a GitHub App. A `klarity-action` that runs the scorer in CI would expand reach. |
| **PR quality badge** | A `[![Klarity Score](badge-url)](dashboard-url)` badge maintainers can put in their README. |
| **Org-level install** | One Klarity install covering all repos in a GitHub org, with per-repo config overrides. |
| **Contributor feedback loop** | When a low-scored PR is later merged, feed that signal back to improve scoring weights over time. |
| **Export / reporting** | CSV export of PR scores for maintainers who want to analyze their repo health externally. |

---

## Flow Diagram (Full System — Including Planned)

```
Contributor opens / updates PR or Issue
        │
        ▼
GitHub fires POST → /api/v1/webhook
        │
        ├── Verify HMAC-SHA256 signature
        ├── Return HTTP 200 immediately
        └── Push job to Redis queue
                │
                ▼
        ARQ Worker picks up job
                │
                ├── pull_request.opened / .edited / .synchronize
                │       │
                │       ├── Fetch PR data, files, commits (GitHub API)
                │       ├── Fetch .klarity.yml (falls back to defaults)
                │       ├── Check ignore list (bots, trusted authors)
                │       │
                │       ├── Heuristic scoring (6 factors → 0–100)
                │       ├── AI slop detection (signal aggregation)
                │       ├── LLM description analysis (Ollama — optional)
                │       ├── Contributor reputation lookup
                │       │
                │       ├── Calculate final score + breakdown
                │       │
                │       ├── Post / update score comment on PR
                │       ├── Apply labels (suspected-ai, needs-tests, etc.)
                │       ├── Save PRScore to DB
                │       └── Notify maintainer if score ≥ threshold
                │
                └── issues.opened / .edited
                        │
                        ├── Embed issue text (nomic-embed-text via Ollama)
                        ├── Query ChromaDB for semantic duplicates
                        ├── Check issue template compliance
                        ├── Classify issue type (bug / feature / question)
                        ├── Apply labels
                        ├── Post duplicate / compliance comment if needed
                        └── Save issue + embedding to DB
                                │
                                ▼
                        Scheduled Jobs (daily/weekly)
                                │
                                ├── Stale checker — mark inactive issues
                                └── Weekly digest — email / Slack / Discord

                                        │
                                        ▼
                        Dashboard (Next.js)
                                │
                                ├── Queue page — all PRs sorted by score
                                ├── Suspected AI page — flagged items
                                ├── Stale page — inactive items
                                ├── Contributors page — reputation view
                                └── Settings page — edit .klarity.yml via UI
```
