# Remaining file additions (apply in **Agent** mode)

Plan mode updated [README.md](../README.md) and [IMPROVEMENTS_SPEC.md](IMPROVEMENTS_SPEC.md). The following new/changed **non-markdown** files are blocked in plan mode—paste or apply in an agent / local editor session.

## New: `requirements-dev.txt`

```
pytest>=7.0.0
```

## New: `tests/test_xeraser_analytics.py`

See full content in [IMPROVEMENTS_SPEC.md](IMPROVEMENTS_SPEC.md) test section, or use this minimal layout:

- `test_parse_tweets_js_minimal` with `tmp_path` + `window.YTD.tweets.part0 = [ { "tweet" : { ... } } ]`
- `test_tweets_activity_by_month` / `test_tweets_source_stats` with in-memory list dicts
- `test_parse_overview_csv` / `test_parse_content_csv` with `tmp_path` files matching column names in `xeraser_analytics.py`

## Patch: [PleaseDaddyElonNotTheBelt.py](../PleaseDaddyElonNotTheBelt.py)

See [IMPROVEMENTS_SPEC.md](IMPROVEMENTS_SPEC.md) for:

- `TOS_LAST_RUN_FILE` + `_load_tos_last_run` / `_save_tos_last_run` + call after `load_tweets` and in `_on_tos_done`
- ToS JSON **retry** with `_TOS_JSON_REPAIR` when `_parse_tos_ids_from_response` returns `None`
- **Follows** progress: `_paginate_user_list` variant that updates `follows_status` each page
- **Tab 4** disclaimer label (heuristic / not legal advice)

## Patch: [.gitignore](../.gitignore)

Add line: `tos_last_run.json`

## Patch: [run.sh](../run.sh)

Prefer `python3 -m venv .venv` and `pip install -r requirements.txt` in instructions; `exec` `.venv/bin/python PleaseDaddyElonNotTheBelt.py`.

## Verify

```bash
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/pytest tests/ -q
```
