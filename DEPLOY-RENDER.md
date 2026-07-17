# Deploy WasteTrack on Render (step-by-step)

## What you get

- Public HTTPS URL (e.g. `https://wastetrack.onrender.com`)
- Free web service plan
- Demo accounts ready (SEED_DEMO_DATA=true by default)
- Optional free Postgres later

**Note:** Free web services **spin down after ~15 minutes** idle. First request after sleep can take 30–60 seconds — normal for free tier.

---

## Part A — Put the project on GitHub

Render deploys from a Git repository.

### 1. Create a GitHub account

If you do not have one: https://github.com/signup

### 2. Create a new empty repository

1. Go to https://github.com/new  
2. Name: `wastetrack` (or any name)  
3. **Public**  
4. Do **not** add README / .gitignore / license (project already has them)  
5. Create repository  

### 3. Push this project (Windows PowerShell)

Open PowerShell in the project folder:

```powershell
cd "C:\Users\Isah Muhammed Isah\waste-management-system"

git init
git add .
git commit -m "Initial WasteTrack production deploy"

# Replace YOUR_USERNAME with your GitHub username
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/wastetrack.git
git push -u origin main
```

GitHub will ask you to sign in (browser or personal access token).

---

## Part B — Deploy on Render

### 1. Sign up

https://dashboard.render.com/register  
Prefer **Sign up with GitHub** (easiest).

### 2. Create Web Service

1. Dashboard → **New +** → **Web Service**  
2. Connect the `wastetrack` GitHub repo  
3. Fill in:

| Field | Value |
|--------|--------|
| **Name** | `wastetrack` |
| **Region** | Oregon (or nearest) |
| **Runtime** | Python 3 |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -c gunicorn.conf.py wsgi:app` |
| **Instance type** | **Free** |

### 3. Environment variables

Add these under **Environment**:

| Key | Value |
|-----|--------|
| `FLASK_ENV` | `production` |
| `BEHIND_PROXY` | `true` |
| `PREFERRED_URL_SCHEME` | `https` |
| `SESSION_COOKIE_SECURE` | `true` |
| `SEED_DEMO_DATA` | `true` |
| `SHOW_DEMO_CREDENTIALS` | `false` |
| `SECRET_KEY` | click **Generate** (or paste a long random string) |

Leave `DATABASE_URL` empty for SQLite demo (simplest).

### 4. Deploy

Click **Create Web Service**. Wait for build logs to show **Live**.

Open the URL Render shows, e.g. `https://wastetrack-xxxx.onrender.com`

Health check: `https://YOUR-URL.onrender.com/health`

---

## Part C — Log in after deploy

With `SEED_DEMO_DATA=true`:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@waste.local` | `admin123` |
| Officer | `officer@waste.local` | `officer123` |
| Resident | `resident@waste.local` | `resident123` |

---

## Optional: Free Postgres (keeps data longer)

Free SQLite on Render can reset when the service rebuilds. For a more solid demo:

1. Render → **New +** → **PostgreSQL** → plan **Free**  
2. After create → **Connect** → copy **Internal Database URL**  
3. Web service → **Environment** → add:

   `DATABASE_URL` = that URL  

4. **Manual Deploy** → **Deploy latest commit**

The app auto-converts `postgres://` to SQLAlchemy’s `postgresql+psycopg://`.

**Free Postgres limits:** ~1 GB, expires after ~30 days (upgrade or backup before then).

---

## Optional: Blueprint deploy

If the repo is connected:

1. **New +** → **Blueprint**  
2. Select repo (uses `render.yaml`)  
3. Confirm env vars and create  

---

## Updating the live site

After code changes:

```powershell
cd "C:\Users\Isah Muhammed Isah\waste-management-system"
git add .
git commit -m "Describe your change"
git push
```

Render auto-deploys from `main` if Auto-Deploy is on.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Build fails on `psycopg` | Ensure `requirements.txt` is the project one; rebuild |
| App crashes on boot | Check logs; confirm `SECRET_KEY` is set |
| 502 / spin-up delay | Free tier cold start — wait 1 minute and refresh |
| No login works | Confirm `SEED_DEMO_DATA=true` or set `ADMIN_EMAIL` / `ADMIN_PASSWORD` |
| Database error | Clear bad `DATABASE_URL` or fix Postgres URL |
| Health check fails | Ensure start command is `gunicorn -c gunicorn.conf.py wsgi:app` |

Logs: Render dashboard → your service → **Logs**.

---

## Defense tip

Before your presentation:

1. Open the site once so it wakes from sleep  
2. Log in as admin and officer to warm the app  
3. Have screenshots ready if campus Wi‑Fi is slow  
