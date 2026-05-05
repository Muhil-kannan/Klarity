# Testing Klarity Locally

This guide walks you through running and testing Klarity end-to-end on your machine.

---

## Prerequisites

- Docker + Docker Compose installed
- A GitHub account
- [ngrok](https://ngrok.com/download) installed (free tier is fine)
- A test GitHub repository (can be private)

---

## Step 1 — Start ngrok

ngrok creates a public HTTPS tunnel to your local machine so GitHub can send webhooks to it.

```bash
ngrok http 8000
```

You'll see output like:

```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

Copy the `https://` URL. You'll need it in the next step.

---

## Step 2 — Create a GitHub App (one-time setup)

1. Go to [github.com/settings/apps/new](https://github.com/settings/apps/new)
2. Fill in:
   - **App name:** `Klarity Dev` (or anything)
   - **Homepage URL:** `http://localhost:8000`
   - **Webhook URL:** `https://YOUR-NGROK-URL/api/v1/webhook`
   - **Webhook secret:** run `openssl rand -hex 32` and paste the output — save it
3. Permissions:
   - Pull requests → Read & Write
   - Issues → Read & Write
   - Contents → Read
   - Metadata → Read
4. Subscribe to events: **Pull request**, **Issues**
5. Click **Create GitHub App**
6. On the next page, scroll down and click **Generate a private key** — a `.pem` file downloads

---

## Step 3 — Configure environment

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and set:

```env
GITHUB_APP_ID=         # shown on your GitHub App page (a number like 123456)
GITHUB_WEBHOOK_SECRET= # the secret you generated in step 2
GITHUB_APP_PRIVATE_KEY=# contents of the .pem file — replace newlines with \n
```

**How to format the private key:**

On Mac/Linux:
```bash
awk 'NF {sub(/\r/, ""); printf "%s\\n",$0;}' your-app.pem
```

On Windows (PowerShell):
```powershell
(Get-Content your-app.pem) -join '\n'
```

Paste the output as the value of `GITHUB_APP_PRIVATE_KEY`.

---

## Step 4 — Start Klarity

```bash
docker compose up
```

Wait for all services to be healthy. You should see:

```
klarity-backend   | INFO  db.initialized
klarity-backend   | INFO  Application startup complete
klarity-worker    | INFO  Starting worker
```

Verify the backend is up:

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","version":"0.1.0"}
```

---

## Step 5 — Install the GitHub App on a test repo

1. Go to your GitHub App settings → **Install App** tab
2. Click **Install** next to your account
3. Choose **Only select repositories** and pick your test repo
4. Click **Install**

---

## Step 6 — Open a test PR

Go to your test repository and open a pull request. Within a few seconds you should see:

1. A Klarity score comment posted on the PR (e.g. "Klarity Score: 45/100 — Needs Work")
2. Labels applied (`needs-tests`, `needs-issue-link`, etc.)

If nothing happens, check the logs:

```bash
docker compose logs -f klarity-worker
```

---

## Step 7 — View the dashboard

Open [http://localhost:3000](http://localhost:3000) in your browser.

> The dashboard requires GitHub OAuth. Set up `dashboard/.env.local` with your GitHub OAuth App credentials to enable login. For quick testing, you can skip the dashboard and just check the PR comments directly on GitHub.

---

## Replaying Webhooks

If a webhook failed or you want to re-test without opening a new PR:

1. Go to your GitHub App settings → **Advanced** tab
2. Find the delivery in the list
3. Click **Redeliver**

This replays the exact same payload — useful for debugging.

---

## Running Unit Tests

```bash
cd backend
pip install -e ".[dev]"
pytest -v
```

Expected output:

```
tests/unit/test_heuristics.py::TestLinkedIssue::test_closes_issue PASSED
tests/unit/test_heuristics.py::TestLinkedIssue::test_fixes_issue PASSED
...
tests/unit/test_slop_detector.py::TestSlopDetector::test_slop_pr_flagged PASSED
...
15 passed in 0.42s
```

---

## Common Issues

**Webhook not received:**
- Make sure ngrok is running and the URL in your GitHub App matches
- Check `docker compose logs klarity-backend` for errors
- Verify the webhook secret matches in `.env` and GitHub App settings

**Score comment not posted:**
- Check `docker compose logs klarity-worker` — the job runs in the background
- Make sure the GitHub App has Read & Write on Pull Requests

**`GITHUB_APP_PRIVATE_KEY` error:**
- Make sure newlines are replaced with `\n` in the `.env` file
- The key should start with `-----BEGIN RSA PRIVATE KEY-----\n`

**Port already in use:**
- Change `8000:8000` to `8001:8000` in `docker-compose.yml` if port 8000 is taken
- Update ngrok to forward to the new port: `ngrok http 8001`
