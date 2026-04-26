# Improvements implementation spec (for agent mode)

Apply these in agent mode; this file is the checklist when `README.md` alone is insufficient.

## 1. README.md (replace content)

- Describe: Tabs 1–10 (Instructions, Auth, Posts, **ToS review**, Deletion, History, Compose, **Follows**, **Blocks & Mutes**, **Analytics**).
- **X API** for Fetch Newer/Older and import; **no** AI/Grok fetch.
- **Tab 4** ToS: optional AI, JSON flags, "Flagged in last ToS review" on Tab 3.
- `pip install -r requirements.txt` (tweepy, matplotlib); Python 3.8+; tk on Linux.
- **Security**: `x_credentials.json` plain text on disk; keep out of git; see `.gitignore`.
- **Local files**: add `tos_last_run.json` if you implement persistence.
- **Tests**: `pip install -r requirements-dev.txt && pytest tests/ -q`
- **Optional packaging**: one paragraph on PyInstaller (out of scope for repo unless script added).
- **Development** note: large monolith; future modular split optional.

## 2. requirements-dev.txt (new)

```
pytest>=7.0.0
```

## 3. tests/test_xeraser_analytics.py (new)

- `test_parse_tweets_js_minimal`: tiny `tweets.js` in `tmp_path` with one tweet object.
- `test_parse_overview_csv` / `test_parse_content_csv` with in-memory or tmp CSV strings using `io.StringIO` or `tmp_path` files.
- `test_tweets_source_stats` / `tweets_activity_by_month` on synthetic list dicts.
- `test_merge` — only if you export helpers; else skip.

## 4. PleaseDaddyElonNotTheBelt.py

### Constants (after `HISTORY_FILE`):

```python
TOS_LAST_RUN_FILE = os.path.join(BASE_DIR, "tos_last_run.json")
```

### `__init__` after `load_tweets()`:

```python
self._load_tos_last_run()
```

### Tab 4 labels (`setup_ai_scrub_tab` intro):

Add second paragraph: *Heuristic; not legal advice. False positives/negatives possible. Always review X’s official rules.*

### ToS: strict retry prompt (class const next to `_TOS_SYSTEM_PROMPT`):

```python
_TOS_JSON_REPAIR = (
    "Return a single JSON object, nothing else, no markdown fences. "
    'Shape: {"flagged":[{"id":"string","level":"low|medium|high","reason":"brief"}]}.'
)
```

### In `_start_ai_scrub` `run()` loop, after `ids = _parse_tos_ids_from_response(text)`:

- If `ids is None` and `text` not empty, call `_call_ai_chat` again with `_TOS_JSON_REPAIR` as system and `user_prompt + "\n\nPrevious reply was not valid JSON."` as user.
- If still `None`, use `set()` and increment `unparseable_batches` counter; append to summary in `_on_tos_done`.
- `acc |= ids` when ids is a set (never None after repair).

### `_save_tos_last_run` / `_load_tos_last_run`

- **Save** in `_on_tos_done`: `{"ids": list(self._tos_flagged_ids), "at": datetime.utcnow().isoformat() + "Z", "summary": "...", "total_rows": n}`.
- **Load** in `_load_tos_last_run`: read file; intersect `ids` with `self.tweets` ids; set `self._tos_flagged_ids`; if `n > 0`, set `ai_scrub_compiled_var` / `ai_scrub_result_var` to short restored text.

### `_thread_fetch_follows` / new `_paginate_user_list_with_status`

- Replace two `_paginate_user_list` calls with a variant that `root.after(0, lambda: follows_status.set(f"Loading following: {len(out)} (page {page})…"))` and same for "followers" between API pages. Keep `time.sleep(1.0)` between follow/follower phases.

## 5. .gitignore

Add: `tos_last_run.json`

## 6. run.sh

- Use `python3` if `python3` in PATH, else `python`.
- If no `.venv`: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt` with message, or `exit 1` with instructions to run `python3 -m venv .venv` and `pip install -r requirements.txt`.
- `exec` `.venv/bin/python" PleaseDaddyElonNotTheBelt.py` from repo root `cd`.

## 7. Optional: `scripts/packaging_notes.md` (one file)

- PyInstaller: `pyinstaller --onefile --noconsole PleaseDaddyElonNotTheBelt.py` — note matplotlib/tk bundling pain on each OS; link to docs.

## 8. Git

Commit: `docs: refresh README, tests, ToS/follows UX, run.sh`

## Appendix: full `tests/test_xeraser_analytics.py`

Create this file verbatim:

```python
"""Unit tests for offline analytics parsers (no GUI, no network)."""
import textwrap

import xeraser_analytics


def test_parse_tweets_js_minimal(tmp_path):
    js = textwrap.dedent(
        """
        window.YTD.tweets.part0 = [ {
        "tweet" : {
        "id_str" : "123",
        "created_at" : "Mon Apr 15 10:00:00 +0000 2024",
        "full_text" : "Hello world",
        "source" : "<a>Web App</a>",
        "retweeted" : false
        }
        } ];
        """
    )
    p = tmp_path / "tweets.js"
    p.write_text(js, encoding="utf-8")
    out = xeraser_analytics.parse_tweets_js(str(p))
    assert len(out) == 1
    t = out[0]
    assert t["id_str"] == "123"
    assert "Hello" in t["full_text"]
    assert t.get("is_retweet") is False


def test_tweets_activity_by_month():
    tweets = [
        {"created_at": "Mon Apr 15 10:00:00 +0000 2024", "id_str": "1"},
        {"created_at": "Tue May 10 10:00:00 +0000 2024", "id_str": "2"},
    ]
    m = xeraser_analytics.tweets_activity_by_month(tweets)
    assert ("2024-04", 1) in m
    assert ("2024-05", 1) in m


def test_tweets_source_stats():
    tweets = [
        {"source": '<a href="http://twitter.com">X for iPhone</a>'},
        {"source": "bad"},
    ]
    s = xeraser_analytics.tweets_source_stats(tweets)
    assert len(s) >= 1
    assert sum(c for _, c in s) == 2


def test_parse_overview_csv(tmp_path):
    csv = (
        'Date,Impressions,Engagements,Likes,Replies,Reposts,New follows,Unfollows,'
        'Bookmarks,Shares,Profile visits,Create Post,Video views,Media views\n'
        '"Fri, Apr 26, 2024",100,10,2,0,0,0,0,0,0,0,0,0,0\n'
    )
    p = tmp_path / "o.csv"
    p.write_text(csv, encoding="utf-8")
    rows = xeraser_analytics.parse_overview_csv(str(p))
    assert len(rows) == 1
    assert rows[0]["impressions"] == 100


def test_parse_content_csv(tmp_path):
    csv = (
        "Post id,Date,Post text,Post Link,Impressions,Engagements,Likes\n"
        "999,2024-04-26,Hi,https://x.com/x/status/999,50,5,1\n"
    )
    p = tmp_path / "c.csv"
    p.write_text(csv, encoding="utf-8")
    rows = xeraser_analytics.parse_content_csv(str(p))
    assert len(rows) == 1
    assert rows[0]["post_id"] == "999"
    assert rows[0]["impressions"] == 50
```
