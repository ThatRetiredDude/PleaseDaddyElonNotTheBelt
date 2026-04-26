# PleaseDaddyElonNotTheBelt – X bulk deleter and account tools

[![CI](https://github.com/ThatRetiredDude/PleaseDaddyElonNotTheBelt/actions/workflows/ci.yml/badge.svg)](https://github.com/ThatRetiredDude/PleaseDaddyElonNotTheBelt/actions/workflows/ci.yml)

Desktop app to manage your own X (Twitter) data using **your** [developer](https://developer.x.com) keys: fetch posts, queue bulk deletes, review history, follow/unfriend, blocks/mutes, and **offline** analytics. Optional **AI** (Tab 4) is for **ToS review only**; loading posts always uses the **X API** or your archive import.

## Features (tabs)

| Tab | Purpose |
|-----|--------|
| 1. Instructions | How to get API keys and a tab overview |
| 2. Authorization | X API keys, **Test User Auth / Test Bearer**; optional **AI** (model, OpenAI-compatible endpoint, token) for **Tab 4** only — not used to download posts |
| 3. My posts & replies | **Fetch Newer** / **Fetch Older** (X API), import archive, search, filters, queue for deletion, **Show → Flagged in last ToS review** after a ToS run |
| 4. ToS review | AI batch review: flags posts that *might* break X rules. Heuristic (not legal advice). Invalid model JSON is retried with a stricter prompt; last flagged ids and summary are saved to `tos_last_run.json` (intersected with your loaded tweets on next launch) |
| 5. Deletion queue | Delete queued posts in bulk |
| 6. Historical deletions | Log of deletions, restore-to-compose actions |
| 7. Compose | Post from the app |
| 8. Follows | Following, followers, mutuals, follow/unfollow (X API; tier may apply). Refresh shows **per-page progress** while lists load |
| 9. Blocks & mutes | List and actions where API allows |
| 10. Analytics (offline) | `tweets.js` + optional Premium **overview** and **content** CSVs; data stays on your machine |

## Requirements

- **Python 3.8+**
- **Dependencies** (see [requirements.txt](requirements.txt)): `tweepy`, `matplotlib`
- **tkinter** — usually bundled; on Linux install the system `python3-tk` / `tk` package
- X API **Basic** tier is often required to **list** your tweets; free tier can still support delete flows depending on X policy

## Setup

```bash
cd path/to/PleaseDaddyElonNotTheBelt
python3 -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
```

After the venv exists and dependencies are installed, you can also run from the repo root with [run.sh](run.sh) (Unix/macOS) or [run.bat](run.bat) (Windows). The scripts expect `.venv` next to the script, install `requirements.txt` if `tweepy` is missing, then start the app.

**Unix / macOS**

```bash
./run.sh
```

**Windows (Command Prompt or `cmd` from the repo root)**

```bat
run.bat
```

Or, with your venv activated:

```bash
python3 PleaseDaddyElonNotTheBelt.py
```

## Security and local files

- **[x_credentials.json](PleaseDaddyElonNotTheBelt.py)** (next to the script) stores API keys in **plain JSON** on disk. It is **gitignored**; keep backups private and do not commit it.
- Other local, gitignored data: [my_tweets.json](PleaseDaddyElonNotTheBelt.py), [deleted_history.json](PleaseDaddyElonNotTheBelt.py), [ai_requests.log](PleaseDaddyElonNotTheBelt.py) (AI debug, no tokens in logs by design), **tos_last_run.json** (last ToS flagged ids + summary), `follows_cache.json` if present. Treat as sensitive; use tight file permissions on your user account. Built-in keychain/encryption is not included.

## Fetch vs delete

- Fetching timelines uses the read path (bearer and/or user auth) with Tweepy.
- Deletes use **user auth** (access token + secret) only.

## Development

- **Unit tests** (offline parsers only, no GUI): with the venv active, `pip install -r requirements-dev.txt` then `pytest tests/ -q` (or `python -m pytest tests/ -q`). Config: [pyproject.toml](pyproject.toml). Tests live under [tests/](tests/).
- **CI:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs those tests on push and pull requests (Python 3.10, 3.12, 3.13, Ubuntu). No API keys are required in CI.
- **Dependabot** ([`.github/dependabot.yml`](.github/dependabot.yml)) proposes monthly updates for pip and GitHub Actions.
- [xeraser_analytics.py](xeraser_analytics.py) holds archive/CSV parsing for Tab 10; the main UI is in [PleaseDaddyElonNotTheBelt.py](PleaseDaddyElonNotTheBelt.py) (single file by design; modular split is optional future work).
- **Optional native packaging** (PyInstaller, etc.): see [scripts/packaging_notes.md](scripts/packaging_notes.md). Not required for normal use.
- Design notes and implementation checklists: [docs/IMPROVEMENTS_SPEC.md](docs/IMPROVEMENTS_SPEC.md), [docs/TESTS_AND_PATCHES.md](docs/TESTS_AND_PATCHES.md).

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
