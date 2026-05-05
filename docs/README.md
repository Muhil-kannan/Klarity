<div align="center">

<img src="https://raw.githubusercontent.com/your-org/klarity/main/docs/assets/banner.png" alt="Klarity Banner" width="100%" />

# Klarity

**AI Triage Assistant for Open Source Maintainers**

Stop drowning in AI-generated PR spam. Klarity automatically scores, labels, and triages every incoming pull request and issue — so you spend time on real contributions, not noise.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Next.js 16](https://img.shields.io/badge/Next.js-16.2-black?logo=next.js)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[**Quick Start**](#quick-start) · [**How It Works**](#how-it-works) · [**Features**](#features) · [**Configuration**](#configuration) · [**Contributing**](#contributing)

</div>

---

## The Problem

Open source maintainers are facing a crisis.

- **17 million** AI-generated pull requests hit GitHub every month — up 325% in 6 months
- **90%** of AI-generated PRs don't meet project quality standards
- The curl project **shut down its entire bug bounty program** because AI slop overwhelmed it
- Maintainers describe it as *"a denial-of-service attack on human attention"*

Volunteer maintainers — already unpaid — now spend the majority of their review time on noise instead of real contributions. They're burning out and leaving open source.

**Klarity fills the gap.** No other open source tool exists specifically to help maintainers triage this flood.

---

## What is Klarity?

Klarity is a **free, open source GitHub App** that acts as an intelligent first-responder for your repository.

It sits between incoming contributions and you — automatically scoring, labeling, and surfacing what actually deserves your attention.

> Klarity reads every incoming PR and issue so you don't have to — and shows you only the ones worth your time.

```
Contributor opens PR
        │
        ▼
GitHub fires webhook → Klarity backend
        │
        ▼
Analysis pipeline runs in background:
  ├── Heuristic checks (tests, linked issue, description, commits, diff size)
  ├── AI slop signal detection
  └── Contributor reputation lookup
        │
        ▼
Score posted as PR comment (0–100) + labels applied
        │
        ▼
Dashboard updated — PR appears in your sorted queue
```

---

## Features

### PR Quality Scoring
Every PR gets a score from 0–100 based on:
- Whether it links to an existing issue
- Whether tests were added or modified
- Quality and length of the PR description
- Commit message quality
- Author's contribution history
- Diff size relative to stated scope

### AI Slop Detection
Flags PRs showing signals of AI generation without human oversight:
- Generic commit messages ("fix bug", "update code")
- No tests despite logic changes
- Boilerplate PR descriptions
- Zero prior contributions + large diff
- Unrelated file changes with no context

### Smart Labels
Automatically applies labels based on analysis:
- `suspected-ai` — AI generation signals detected
- `needs-tests` — logic changed but no tests added
- `needs-issue-link` — PR not linked to an issue
- `low-quality` — score below threshold

### Maintainer Dashboard
A fast, dark-mode web UI showing your full PR queue sorted by score. Filter by score range, suspected AI, or quality tier. See what needs attention at a glance.

### Zero Cloud Dependency
All analysis runs locally. No PR content is sent to external APIs. Fully self-hostable via Docker Compose.

---

## Quick Start

### What you need

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- A GitHub account (to create a GitHub App)
- [ngrok](https://ngrok.com/download) for local dev — or a VPS/server with a public URL for production

### Step 1 — Clone the repo

```bash
git clone https://github.com/your-org/klarity.git
cd klarity
```

### Step 2 — Create a GitHub App

1. Go to [github.com/settings/apps/new](https://github.com/settings/apps/new)
2. Fill in:
   - **App name:** `Klarity` (or any name you like)
   - **Homepage URL:** `http://localhost:8000`
   - **Webhook URL:** your ngrok URL + `/api/v1/webhook`
     - Start ngrok first: `ngrok http 8000`
     - Copy the `https://` URL, e.g. `https://abc123.ngrok.io/api/v1/webhook`
   - **Webhook secret:** generate a random string (e.g. `openssl rand -hex 32`) and save it
3. Set permissions:
   - Pull requests → **Read & Write**
   - Issues → **Read & Write**
   - Contents → **Read**
   - Metadata → **Read**
4. Subscribe to events: **Pull request**, **Issues**
5. Click **Create GitHub App**
6. On the app page, click **Generate a private key** — save the `.pem` file

### Step 3 — Configure environment

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in:

```env
GITHUB_APP_ID=123456                          # from your GitHub App page
GITHUB_WEBHOOK_SECRET=your-secret-here        # the secret from step 2
GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----
```

For the private key: open the `.pem` file, copy the contents, and replace every newline with `\n`.

### Step 4 — Start Klarity

```bash
docker compose up
```

This starts:
- `klarity-backend` on port `8000` — the FastAPI webhook receiver + scoring engine
- `klarity-worker` — the background job processor
- `klarity-redis` — the job queue
- `klarity-dashboard` on port `3000` — the web UI

### Step 5 — Install the GitHub App on your repo

1. Go to your GitHub App settings → **Install App**
2. Install it on the repository you want to monitor
3. Open a pull request on that repo
4. Within seconds, Klarity will post a score comment and apply labels

**That's it.** Your queue is live at [http://localhost:3000](http://localhost:3000).

---

## Testing Locally

### Verify the backend is running

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","version":"0.1.0"}
```

### Simulate a webhook event

You can replay a real webhook from GitHub's App settings page:
1. Go to your GitHub App → **Advanced** tab
2. Find a recent delivery and click **Redeliver**

Or use the GitHub CLI to open a test PR on a repo with Klarity installed.

### Run the test suite

```bash
cd backend
pip install -e ".[dev]"
pytest
```

### Development mode (hot reload)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

Changes to `backend/app/` and `dashboard/` reload automatically.

---

## Configuration

Add a `.klarity.yml` file to the root of your repository to customize behavior. Everything has sensible defaults — zero config required to get started.

```yaml
# .klarity.yml
klarity:
  scoring:
    linked_issue_weight: 15
    tests_changed_weight: 20
    description_quality_weight: 15
    commit_quality_weight: 20
    author_history_weight: 20
    diff_size_weight: 10

  ai_detection:
    enabled: true
    slop_threshold: 5

  auto_responses:
    no_linked_issue: >
      Hi @{author}! Could you link this PR to an existing issue?
    suspected_ai: >
      Hi @{author}! Could you confirm you've reviewed every line of this PR?

  features:
    scoring: true
    ai_detection: true
```

See [`.klarity.yml.example`](../.klarity.yml.example) for the full reference.

---

## Architecture

```
klarity/
├── backend/          # Python 3.12 + FastAPI
│   └── app/
│       ├── api/      # Webhook receiver + dashboard API
│       ├── scoring/  # Heuristic engine + slop detector
│       ├── github/   # GitHub App auth + API client
│       ├── jobs/     # ARQ background workers
│       └── db/       # SQLModel + SQLite/PostgreSQL
│
├── dashboard/        # Next.js 16.2
│   ├── app/          # App Router pages
│   ├── components/   # Queue table, score badge, filters
│   └── lib/          # API client, auth, utilities
│
└── docker-compose.yml  # Full stack in one command
```

**Tech stack:**
- Backend: Python 3.12, FastAPI, Redis + ARQ, SQLModel, SQLite
- Frontend: Next.js 16.2, Tailwind CSS, shadcn/ui, NextAuth.js
- Infrastructure: Docker Compose, GitHub Actions

---

## Roadmap

| Version | Status | What's included |
|---|---|---|
| v0.1 | ✅ Current | Heuristic scorer, PR comments, labels, Docker setup |
| v0.2 | Planned | LLM scoring (Ollama), AI slop detector, issue triage, contributor reputation |
| v0.3 | Planned | Full dashboard, weekly digest, Slack/Discord notifications |
| v1.0 | Planned | GitHub Marketplace listing, cloud-hosted option, PostgreSQL |

---

## Contributing

Klarity is built for the open source community — contributions are very welcome.

See [CONTRIBUTING.md](CONTRIBUTING.md) to get started. Good first issues are labeled [`good-first-issue`](https://github.com/your-org/klarity/labels/good-first-issue).

---

## License

MIT — see [LICENSE](../LICENSE) for details.

---

<div align="center">
  <sub>Built for maintainers, by maintainers. If Klarity saves you time, consider giving it a ⭐</sub>
</div>
