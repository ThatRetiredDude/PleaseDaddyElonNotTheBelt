"""Local parsers for X archive and Premium analytics exports (no network)."""
import csv
import json
import re
from collections import Counter
from datetime import datetime


def parse_tweets_js(path: str):
    """
    Read archive tweets.js: window.YTD.tweets.part0 = [ {...}, ... ];
    Returns list of {id_str, created_at, full_text, source, is_retweet, is_reply, raw}.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    text = re.sub(
        r"^window\.YTD\.tweets\.part\d+\s*=\s*",
        "",
        text,
        count=1,
        flags=re.DOTALL | re.MULTILINE,
    )
    t = text.strip()
    if t.endswith(";"):
        t = t[:-1].strip()
    dec = json.JSONDecoder()
    if not t.startswith("["):
        b = t.find("[")
        if b < 0:
            raise ValueError("Could not find JSON array in tweets.js")
        t = t[b:]
    data, _ = dec.raw_decode(t)
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array in tweets.js")
    out = []
    for item in data:
        t = item.get("tweet")
        if not isinstance(t, dict):
            continue
        id_str = str(t.get("id_str") or t.get("id") or "")
        if not id_str:
            continue
        created = t.get("created_at")
        is_ret = bool(t.get("retweeted", False)) or t.get("retweeted_status") is not None
        is_repl = bool(
            t.get("in_reply_to_status_id") or t.get("in_reply_to_status_id_str")
        )
        body = t.get("full_text") or t.get("text") or ""
        src = t.get("source") or ""
        out.append(
            {
                "id_str": id_str,
                "created_at": created,
                "full_text": str(body)[:2000],
                "source": src,
                "is_retweet": is_ret,
                "is_reply": is_repl,
                "raw": t,
            }
        )
    return out


def _parse_overview_date(s):
    s = (s or "").strip().strip('"')
    if not s:
        return None
    for fmt in ("%a, %b %d, %Y",):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def parse_overview_csv(path: str):
    """
    X Premium outline export. Columns: Date, Impressions, Likes, ...
    Returns list of {date, impressions, ...} with numeric fields as int.
    """
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        rows = []
        for row in r:
            dt = _parse_overview_date(row.get("Date", ""))
            if not dt:
                continue
            def num(k):
                try:
                    v = (row.get(k) or "0").replace(",", "").strip()
                    return int(v or 0)
                except (ValueError, TypeError):
                    return 0
            rows.append(
                {
                    "date": dt,
                    "impressions": num("Impressions"),
                    "likes": num("Likes"),
                    "engagements": num("Engagements"),
                    "bookmarks": num("Bookmarks"),
                    "shares": num("Shares"),
                    "new_follows": num("New follows"),
                    "unfollows": num("Unfollows"),
                    "replies": num("Replies"),
                    "reposts": num("Reposts"),
                    "profile_visits": num("Profile visits"),
                    "create_post": num("Create Post"),
                    "video_views": num("Video views"),
                    "media_views": num("Media views"),
                }
            )
        rows.sort(key=lambda x: x["date"])
    return rows


def parse_content_csv(path: str):
    """
    Per-post analytics CSV. Skips bad rows (missing id, undefined in URL).
    """
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.DictReader(f)
        need = "Post id"
        out = []
        for row in r:
            pid = (row.get(need) or row.get("Post id") or "").strip()
            if not pid or not str(pid).isdigit():
                continue
            def num(*keys):
                for k in keys:
                    if k in row and row.get(k) not in (None, ""):
                        try:
                            s = str(row.get(k) or "0").strip()
                            s = re.sub(r"[^\d\-.]", "", s) or "0"
                            if not s or s in ("-", "."):
                                return 0
                            return int(float(s))
                        except (ValueError, TypeError):
                            pass
                return 0
            out.append(
                {
                    "post_id": str(pid),
                    "date": row.get("Date", "") or "",
                    "text": (row.get("Post text") or row.get("Post Text") or "")[:500],
                    "link": row.get("Post Link") or "",
                    "impressions": num("Impressions", "impressions"),
                    "likes": num("Likes"),
                    "engagements": num("Engagements"),
                }
            )
    return out


def tweets_activity_by_month(tweets):
    c = Counter()
    for t in tweets:
        ca = t.get("created_at")
        if not ca or not isinstance(ca, str):
            continue
        try:
            d = datetime.strptime(ca, "%a %b %d %H:%M:%S +0000 %Y")
            key = d.strftime("%Y-%m")
        except (ValueError, TypeError):
            try:
                d = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                key = d.strftime("%Y-%m")
            except (ValueError, TypeError):
                continue
        c[key] += 1
    return sorted(c.items())


def tweets_source_stats(tweets):
    def strip_src(html: str) -> str:
        m = re.search(r">([^<]+)<", html or "")
        if m:
            return m.group(1).strip()
        s = re.sub(r"<[^>]+>", " ", html or "")
        return (s.strip() or "Unknown")[:80]
    c = Counter()
    for t in tweets:
        c[strip_src(t.get("source", ""))] += 1
    return sorted(c.items(), key=lambda x: -x[1])[:25]
