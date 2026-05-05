# Contributing to Klarity

First off — thank you. Klarity exists to help open source maintainers, and it's built by the same community it serves. Every contribution matters.

---

## Ways to Contribute

- **Report bugs** — open an issue with steps to reproduce
- **Suggest features** — open an issue describing the use case
- **Fix bugs** — pick up any issue labeled `bug`
- **Build features** — check issues labeled `good-first-issue` or `help-wanted`
- **Improve docs** — typos, clarity, missing steps — all welcome
- **Write tests** — more coverage is always useful

---

## Before You Start

1. Check [open issues](https://github.com/your-org/klarity/issues) to avoid duplicate work
2. For significant changes, open an issue first to discuss the approach
3. For small fixes (typos, docs, minor bugs), just open a PR directly

---

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 22+
- Docker + Docker Compose
- Git

### 1. Fork and clone

```bash
git clone https://github.com/YOUR-USERNAME/klarity.git
cd klarity
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 3. Set up the dashboard

```bash
cd dashboard
npm install
```

### 4. Configure environment

```bash
cp backend/.env.example backend/.env
cp dashboard/.env.local.example dashboard/.env.local
```

Fill in your GitHub App credentials (see [docs/README.md](README.md#step-2--create-a-github-app)).

### 5. Start the stack

```bash
# Full stack with hot reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or run backend directly (no Docker)
cd backend
uvicorn app.main:app --reload --port 8000

# And the dashboard
cd dashboard
npm run dev
```

---

## Running Tests

```bash
cd backend
pytest                    # run all tests
pytest tests/unit/        # unit tests only
pytest -v                 # verbose output
```

---

## Code Style

**Backend (Python):**
- Formatter: `ruff format`
- Linter: `ruff check`
- Types: `mypy` (not strict, but type hints are expected on all public functions)

```bash
cd backend
ruff format .
ruff check .
```

**Frontend (TypeScript):**
- Linter: `eslint` via `npm run lint`
- No separate formatter config — Next.js defaults

---

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Write a clear description of what changed and why
- Link to the issue it addresses (`Closes #N`)
- Add tests for new behavior
- Make sure `pytest` passes before opening the PR
- Keep commit messages descriptive (not "fix stuff")

---

## Project Structure

```
klarity/
├── backend/app/
│   ├── scoring/        # Scoring engine — good place to start
│   ├── github/         # GitHub API client
│   ├── jobs/           # Background workers
│   └── api/v1/routes/  # HTTP endpoints
│
├── dashboard/
│   ├── app/            # Next.js pages
│   └── components/     # UI components
│
└── docs/               # Documentation
```

The scoring engine (`backend/app/scoring/`) is the best place to start if you want to understand how Klarity works.

---

## Good First Issues

Look for issues tagged [`good-first-issue`](https://github.com/your-org/klarity/labels/good-first-issue). These are scoped, well-defined, and don't require deep knowledge of the codebase.

Examples of good first contributions:
- Add a new heuristic check to the scoring engine
- Improve a default auto-response message
- Add a missing test case
- Fix a typo or improve a doc section

---

## Questions?

Open a [GitHub Discussion](https://github.com/your-org/klarity/discussions) or drop a comment on the relevant issue.
