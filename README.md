# WasteTrack

**Waste Management Reporting & Collection Optimization System**

Final-year project prototype — Department of Computer Science, Abubakar Tafawa Balewa University Bauchi.

Web application for:

- **Residents** — geolocated waste reports (category, description, map, optional photo) + status tracking  
- **Administrators** — verify, assign, schedule, analytics, route optimization  
- **Collection officers** — task list, start/complete workflow  

Optimization uses **Haversine distance + nearest-neighbour** with urgency preference.

---

## Quick start (development)

```bash
cd waste-management-system
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
# Optional: leave defaults for local demo (SEED_DEMO_DATA is true in development)

python run.py
```

Open **http://127.0.0.1:5000**

### Demo accounts (development only)

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@waste.local` | `admin123` |
| Officer | `officer@waste.local` | `officer123` |
| Resident | `resident@waste.local` | `resident123` |

---

## Production & deploy

This repo is **production-ready**. See **[DEPLOY.md](DEPLOY.md)** for:

- Environment variables and bootstrap admin  
- Windows Waitress / Linux Gunicorn  
- Docker Compose  
- Nginx + systemd  
- Render.com / PaaS  
- Security checklist  

**Short production run (Docker):**

```bash
cp .env.example .env
# set SECRET_KEY and ADMIN_PASSWORD
docker compose up -d --build
```

**Short production run (Windows):**

```powershell
.\scripts\start-prod.ps1
```

**Health check:** `GET /health`

---

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, Flask |
| ORM / DB | SQLAlchemy, SQLite (default) or PostgreSQL |
| Auth | Flask-Login (roles: resident, officer, admin) |
| UI | Bootstrap 5, Leaflet + OpenStreetMap |
| Prod server | Gunicorn (Linux) / Waitress (Windows) |
| Containers | Docker, Docker Compose |

---

## Project layout

```
waste-management-system/
├── app/                 # Application package
│   ├── routes/          # HTTP blueprints
│   ├── services/        # Optimization logic
│   ├── templates/       # Jinja2 UI
│   └── static/          # CSS, JS, uploads
├── deploy/              # Nginx + systemd examples
├── scripts/             # start-prod.ps1 / start-prod.sh
├── instance/            # SQLite DB (runtime)
├── wsgi.py              # Production entrypoint
├── gunicorn.conf.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── run.py               # Dev server only
├── README.md
└── DEPLOY.md
```

---

## Status workflow

```
submitted → verified → assigned → scheduled → in_progress → completed
                 ↘ rejected
```

Every transition is stored in status history.

---

## Out of scope (by design)

IoT bin sensors, payments, government ID integration, live fleet GPS, full multi-vehicle industrial VRP.

---

## License

Academic / educational use for the final-year project.
