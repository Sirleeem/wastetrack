import re
import urllib.request

urls = [
    "https://mbasic.facebook.com/profile.php?id=100069222459121",
    "https://www.facebook.com/plugins/post.php?href=https%3A%2F%2Fwww.facebook.com%2F100069222459121%2Fposts%2F1379400754377327%2F",
]

for u in urls:
    print("===", u)
    req = urllib.request.Request(
        u,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
        print("len", len(html))
        for pat in [
            r'og:image" content="([^"]+)"',
            r"https://scontent[^\"'\s<>]+",
            r"https://[^\"'\s<>]*fbcdn[^\"'\s<>]+",
        ]:
            found = re.findall(pat, html)
            print(pat[:30], "->", len(found))
            for x in found[:8]:
                print(" ", x[:180])
    except Exception as e:
        print("ERR", e)
