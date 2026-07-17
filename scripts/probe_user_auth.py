import http.cookiejar
import re
import urllib.error
import urllib.request
from urllib.parse import urlencode

BASE = "https://wastetrack-nd71.onrender.com"


def sess():
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op


def get(op, path):
    r = op.open(BASE + path, timeout=90)
    return r.status, r.geturl(), r.read().decode("utf-8", "replace")


def post(op, path, data):
    req = urllib.request.Request(BASE + path, data=urlencode(data).encode(), method="POST")
    try:
        r = op.open(req, timeout=90)
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, BASE + path, e.read().decode("utf-8", "replace")


def alerts(body):
    found = re.findall(r'class="alert[^"]*"[^>]*>(.*?)</div>', body, re.S)
    return [" ".join(a.split())[:180] for a in found]


def main():
    op = sess()
    st, url, body = get(op, "/auth/setup?key=bauchi2026setup")
    print("SETUP GET", st, url.replace(BASE, ""))
    print("  form role:", "Collection officer" in body)
    print("  blocked page:", "Setup is locked" in body)
    print("  setup_key field:", "setup_key" in body)
    print("  alerts:", alerts(body))

    # Create/update officer via setup
    op = sess()
    st, url, body = post(
        op,
        "/auth/setup",
        {
            "setup_key": "bauchi2026setup",
            "name": "Site Officer",
            "email": "officer@wastetrack.xyz",
            "password": "Officer123!",
            "role": "officer",
        },
    )
    print("SETUP POST officer", st, url.replace(BASE, ""))
    print("  alerts:", alerts(body))

    # Create/update admin via setup
    op = sess()
    st, url, body = post(
        op,
        "/auth/setup",
        {
            "setup_key": "bauchi2026setup",
            "name": "Site Admin",
            "email": "admin@wastetrack.xyz",
            "password": "Admin123!",
            "role": "admin",
        },
    )
    print("SETUP POST admin", st, url.replace(BASE, ""))
    print("  alerts:", alerts(body))

    # Try logins
    for email, pw in [
        ("admin@wastetrack.xyz", "Admin123!"),
        ("officer@wastetrack.xyz", "Officer123!"),
        ("admin@waste.local", "admin123"),
        ("officer@waste.local", "officer123"),
    ]:
        op = sess()
        st, url, body = post(op, "/auth/login", {"email": email, "password": pw})
        print("LOGIN", email, "->", url.replace(BASE, ""), "alerts:", alerts(body)[:1])


if __name__ == "__main__":
    main()
