# Self-Hosting Klarity

Klarity is designed to be self-hosted. This guide covers deploying it on a VPS or home server so GitHub can reach it without ngrok.

---

## Requirements

- A server with a public IP address (any VPS — DigitalOcean, Hetzner, Linode, etc.)
- Docker + Docker Compose installed on the server
- A domain name (optional but recommended for HTTPS)
- Port 80 and 443 open in your firewall

---

## Option 1 — Simple VPS Deployment

### 1. SSH into your server and clone the repo

```bash
git clone https://github.com/your-org/klarity.git
cd klarity
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
cp dashboard/.env.local.example dashboard/.env.local
```

Edit `backend/.env`:
```env
ENVIRONMENT=production
GITHUB_APP_ID=your_app_id
GITHUB_WEBHOOK_SECRET=your_secret
GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----
DATABASE_URL=sqlite+aiosqlite:///./data/klarity.db
REDIS_URL=redis://redis:6379
LOG_FORMAT=json
```

Edit `dashboard/.env.local`:
```env
NEXTAUTH_URL=https://your-domain.com
NEXTAUTH_SECRET=your-random-secret
GITHUB_CLIENT_ID=your_oauth_app_client_id
GITHUB_CLIENT_SECRET=your_oauth_app_client_secret
BACKEND_URL=http://backend:8000
```

### 3. Start the stack

```bash
docker compose up -d
```

### 4. Point your GitHub App webhook to your server

Update the webhook URL in your GitHub App settings to:
```
http://YOUR-SERVER-IP:8000/api/v1/webhook
```

Or with a domain:
```
https://your-domain.com/api/v1/webhook
```

---

## Option 2 — With HTTPS (Recommended for Production)

Use the included nginx config as a reverse proxy with Let's Encrypt.

### 1. Install Certbot

```bash
apt install certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

### 2. Update nginx config

Edit `nginx/nginx.conf` to use your domain and SSL certificate paths.

### 3. Add nginx to docker-compose

Uncomment the nginx service in `docker-compose.yml` (or add it manually):

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
  depends_on:
    - backend
    - dashboard
  networks:
    - klarity_net
```

---

## Keeping Klarity Updated

```bash
git pull
docker compose down
docker compose up -d --build
```

---

## Monitoring

Check service health:
```bash
docker compose ps
docker compose logs -f klarity-worker
```

Check the health endpoint:
```bash
curl https://your-domain.com/api/v1/health
```

---

## Using PostgreSQL (Optional)

For higher traffic or multi-user deployments, switch from SQLite to PostgreSQL.

Add to `docker-compose.yml`:
```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: klarity
    POSTGRES_USER: klarity
    POSTGRES_PASSWORD: your-db-password
  volumes:
    - postgres_data:/var/lib/postgresql/data
  networks:
    - klarity_net
```

Update `backend/.env`:
```env
DATABASE_URL=postgresql+asyncpg://klarity:your-db-password@postgres:5432/klarity
```

Add `asyncpg` to `backend/pyproject.toml` dependencies.
