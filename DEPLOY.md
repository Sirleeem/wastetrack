# WasteTrack - Production & Deployment Guide

This project is deploy-ready with:

| Artifact | Purpose |
|----------|---------|
| `wsgi.py` | Production WSGI entrypoint |
| `gunicorn.conf.py` | Linux/container process manager |
| `waitress` | Windows-friendly WSGI server |
| `Dockerfile` + `docker-compose.yml` | Container deploy |
| `.env.example` | Configuration template |
| `Procfile` / `render.yaml` | PaaS (Render, Heroku-style) |
| `deploy/nginx.conf.example` | Reverse proxy |
| `deploy/wastetrack.service.example` | systemd on Linux VPS |
| `/health` | Health check for load balancers |

---

## 1. Required production settings

Copy the template and edit:

```bash
cp .env.example .env
```

**Minimum variables:**

```env
FLASK_ENV=production
SECRET_KEY=<long-random-hex>
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=<strong-password>
SEED_DEMO_DATA=false
SHOW_DEMO_CREDENTIALS=false
BEHIND_PROXY=true
PREFERRED_URL_SCHEME=https
SESSION_COOKIE_SECURE=true
```

Generate a secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

On first start with an empty database, the app creates the admin user from `ADMIN_EMAIL` / `ADMIN_PASSWORD`.

> Never set `SEED_DEMO_DATA=true` on a public server (it creates weak demo accounts).

---

## 2. Local production-style run

### Windows (Waitress)

```powershell
cd waste-management-system
copy .env.example .env
# Edit .env: SECRET_KEY, ADMIN_PASSWORD, FLASK_ENV=production
# For HTTP-only local test: SESSION_COOKIE_SECURE=false  BEHIND_PROXY=false
.\scripts\start-prod.ps1
```

### Linux / macOS (Gunicorn)

```bash
cd waste-management-system
cp .env.example .env
# Edit .env
chmod +x scripts/start-prod.sh
./scripts/start-prod.sh
```

Open `http://127.0.0.1:8000` and `http://127.0.0.1:8000/health`.

---

## 3. Docker (recommended portable deliverable)

```bash
cp .env.example .env
# Set SECRET_KEY and ADMIN_PASSWORD in .env
# For plain HTTP on localhost, set:
#   SESSION_COOKIE_SECURE=false
#   BEHIND_PROXY=false

docker compose up -d --build
curl http://127.0.0.1:8000/health
```

Data is stored in Docker volumes:

- `wastetrack_data` → SQLite under `/app/instance`
- `wastetrack_uploads` → report photos

To use PostgreSQL, uncomment the `db` service in `docker-compose.yml` and set:

```env
DATABASE_URL=postgresql://wastetrack:wastetrack@db:5432/wastetrack
```

---

## 4. Linux VPS (Nginx + systemd + Gunicorn)

1. Copy project to `/opt/wastetrack`
2. Create venv, install `requirements.txt`
3. Create `.env` with production values
4. Install unit:

```bash
sudo cp deploy/wastetrack.service.example /etc/systemd/system/wastetrack.service
# Edit paths/user
sudo systemctl daemon-reload
sudo systemctl enable --now wastetrack
```

5. Configure Nginx from `deploy/nginx.conf.example`
6. Issue TLS with Certbot (`certbot --nginx`)
7. Keep `BEHIND_PROXY=true` and `SESSION_COOKIE_SECURE=true`

---

## 5. Render.com

1. Push repository to GitHub
2. New → Blueprint → select repo (`render.yaml`)
3. Set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in the dashboard
4. Deploy; health check path is `/health`

Or manual Web Service:

- Build: `pip install -r requirements.txt`
- Start: `gunicorn -c gunicorn.conf.py wsgi:app`
- Env: `FLASK_ENV=production`, `SECRET_KEY`, `DATABASE_URL`, admin vars

---

## 6. Database choices

| Option | When to use |
|--------|-------------|
| **SQLite** (default) | Single-server demos, defense laptop, low traffic |
| **PostgreSQL** | Multi-user production, concurrent writers, PaaS |

Set `DATABASE_URL` for Postgres. The app rewrites `postgres://` → `postgresql+psycopg://` automatically.

---

## 7. Security checklist

- [ ] Strong unique `SECRET_KEY`
- [ ] Strong `ADMIN_PASSWORD`; change after first login if shared during setup
- [ ] `SEED_DEMO_DATA=false` and demo credentials hidden
- [ ] HTTPS terminated at proxy; `SESSION_COOKIE_SECURE=true`
- [ ] `BEHIND_PROXY=true` so Flask sees real client scheme/IP
- [ ] Uploads limited to 5 MB images (configured)
- [ ] Firewall only 80/443 public; app listens on localhost:8000 when using Nginx
- [ ] Regular OS/package updates; backup `instance/` and `uploads/`

---

## 8. Health & ops

```bash
curl -s http://127.0.0.1:8000/health
# {"status":"ok","database":"up","service":"wastetrack"}
```

Logs:

- Gunicorn: stdout/stderr (captured by Docker/systemd)
- Application: Python logging at INFO in production

Backups (SQLite):

```bash
cp instance/waste_management.db backups/waste_$(date +%Y%m%d).db
```

---

## 9. Development vs production

| | Development | Production |
|--|-------------|------------|
| Entry | `python run.py` | `wsgi.py` + Gunicorn/Waitress |
| Env | `FLASK_ENV=development` | `FLASK_ENV=production` |
| Debug | On | Off |
| Demo seed | On by default | Off |
| Cookies | HTTP ok | Secure (HTTPS) |

---

## 10. Academic submission package

Include in your deliverable zip/USB:

```
waste-management-system/
  app/ ...
  deploy/
  scripts/
  Dockerfile
  docker-compose.yml
  wsgi.py
  gunicorn.conf.py
  requirements.txt
  .env.example
  README.md
  DEPLOY.md
  Procfile
  render.yaml
```

Do **not** include: `.env`, `.venv/`, `instance/*.db` with real passwords, or production secrets.
