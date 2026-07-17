import http.cookiejar
import re
import urllib.error
import urllib.request
from urllib.parse import urlencode

BASE = "https://wastetrack-nd71.onrender.com"


def session():
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0")]
    return op


def post(op, path, data):
    req = urllib.request.Request(BASE + path, data=urlencode(data).encode(), method="POST")
    try:
        r = op.open(req, timeout=90)
        return r.status, r.geturl(), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, BASE + path, e.read().decode("utf-8", "replace")


def get(op, path):
    r = op.open(BASE + path, timeout=90)
    return r.status, r.geturl(), r.read().decode("utf-8", "replace")


def alerts(body: str):
    found = re.findall(r'class="alert[^"]*"[^>]*>(.*?)</div>', body, re.S)
    return [" ".join(a.split())[:160] for a in found]


def main():
    for email, pw in [
        ("admin@waste.local", "admin123"),
        ("officer@waste.local", "officer123"),
        ("resident@waste.local", "resident123"),
    ]:
        op = session()
        st, url, body = post(op, "/auth/login", {"email": email, "password": pw})
        print("LOGIN", email, st, url.replace(BASE, ""))
        print("  alerts:", alerts(body))
        print(
            "  markers:",
            {
                "Operations": "Operations" in body,
                "desk": "desk" in body.lower(),
                "Today": "Today" in body,
                "Hello": "Hello" in body,
                "Sign in": "Sign in" in body and "Welcome back" not in body,
            },
        )

    op = session()
    st, url, body = get(op, "/auth/setup")
    print("SETUP", st)
    print("  has setup_key field:", "setup_key" in body)
    print("  has role select:", "Collection officer" in body)
    print("  flash locked:", "locked" in body.lower())

    op = session()
    st, url, body = get(op, "/")
    print("HOME", st)
    print("  landing headline:", "Report refuse where you live" in body)
    print("  admin dashboard only:", "Operations desk" in body and "Report refuse where you live" not in body)

    # static image sizes
    for path in [
        "/static/images/basepa/hero.jpg",
        "/static/images/basepa/street-cleanup.jpg",
        "/static/css/style.css",
    ]:
        op = session()
        try:
            r = op.open(BASE + path, timeout=60)
            print("STATIC", path, r.status, "len", r.headers.get("Content-Length") or len(r.read()))
        except Exception as e:
            print("STATIC", path, "ERR", e)


if __name__ == "__main__":
    main()
