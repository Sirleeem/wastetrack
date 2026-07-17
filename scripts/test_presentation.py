import os
import re
from pathlib import Path

p = Path("instance/pres_test.db")
if p.exists():
    p.unlink()

os.environ["FLASK_ENV"] = "production"
os.environ["SECRET_KEY"] = "presentation-secret-key-32chars-min"
os.environ["SESSION_COOKIE_SECURE"] = "false"
os.environ["BEHIND_PROXY"] = "false"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["ADMIN_EMAIL"] = "admin@wastetrack.xyz"
os.environ["ADMIN_PASSWORD"] = "Admin123!"
os.environ["OFFICER_EMAIL"] = "officer@wastetrack.xyz"
os.environ["OFFICER_PASSWORD"] = "Officer123!"
os.environ["DATABASE_URL"] = "sqlite:///" + p.resolve().as_posix()

from app import create_app

app = create_app()
c = app.test_client()

r = c.get("/")
assert r.status_code == 200
body = r.get_data(as_text=True)
assert "Report refuse where you live" in body
assert "Admin sign-in" not in body
assert "Officer sign-in" not in body
assert "Demo access" not in body
assert "admin@waste.local" not in body
assert "academic software prototype" not in body.lower()

r = c.get("/auth/login")
m = re.search(r'name="csrf_token" value="([^"]+)"', r.get_data(as_text=True))
assert m, "csrf missing on login"
token = m.group(1)
r = c.post(
    "/auth/login",
    data={"email": "admin@wastetrack.xyz", "password": "Admin123!", "csrf_token": token},
    follow_redirects=True,
)
assert r.status_code == 200
text = r.get_data(as_text=True)
assert "Operations" in text or "desk" in text.lower() or "dashboard" in text.lower()
print("PASS presentation checks")
