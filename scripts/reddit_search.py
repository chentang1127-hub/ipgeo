"""Search Reddit for IP geolocation discussions using Scrapling."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from scrapling import Fetcher
import urllib.request

# Reddit's public JSON API doesn't need auth for reading
QUERIES = [
    "ip geolocation api free",
    "ip geolocation API recommendation",
    "best IP geolocation",
    "ipinfo alternative cheaper",
]

f = Fetcher(auto_match=False)

for query in QUERIES:
    url = f"https://www.reddit.com/search.json?q={urllib.request.quote(query)}&sort=comments&limit=8&t=year"
    print(f"\n{'='*60}")
    print(f"  {query}")
    print(f"{'='*60}")
    try:
        resp = f.get(url, timeout=15)
        data = json.loads(resp.text)
        for post in data.get('data', {}).get('children', []):
            p = post['data']
            print(f"\n  r/{p.get('subreddit','?')} | {p.get('score',0)} pts | {p.get('num_comments',0)} comments")
            print(f"  {p.get('title','')}")
            print(f"  https://reddit.com{p.get('permalink','')}")
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
