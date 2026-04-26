# PleaseDaddyElonNotTheBelt – X bulk deleter and account tools

[![CI](https://github.com/ThatRetiredDude/PleaseDaddyElonNotTheBelt/actions/workflows/ci.yml/badge.svg)](https://github.com/ThatRetiredDude/PleaseDaddyElonNotTheBelt/actions/workflows/ci.yml)

Desktop app to manage your own X (Twitter) data using **your** [developer](https://developer.x.com) keys: fetch posts, queue bulk deletes, review history, follow/unfriend, blocks/mutes, and **offline** analytics. Optional **AI** (Tab 4) is for **ToS review only**; loading posts always uses the **X API** or your archive import.

## Features (tabs)

| Tab | Purpose |
|-----|--------|
| 1. Instructions | How to get API keys and a tab overview |
| 2. Authorization | X API keys; **Store in OS keychain** (default when available) or plain `x_credentials.json`. **Test User Auth / Test Bearer**; optional **AI** (model, endpoint, token) for **Tab 4** only — not used to download posts |
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
- **Dependencies** (see [requirements.txt](requirements.txt)): `tweepy`, `matplotlib`, `keyring` (saves X + AI creds in the system keychain when the checkbox in Tab 2 is on; falls back to JSON)
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
# or, same behavior:
python3 -m pde
```

## Project layout

- **[PleaseDaddyElonNotTheBelt.py](PleaseDaddyElonNotTheBelt.py)** — small launcher: dependency check, then `pde.app.main()`.
- **`pde/`** — `app.py` (main window), [paths](pde/paths.py), [constants/AI model lists](pde/constants.py), [ToS batching](pde/ai_batching.py), [dependency check](pde/deps.py), [keyring + file credentials](pde/secure_creds.py).
- **[xeraser_analytics.py](xeraser_analytics.py)** — offline `tweets.js` and Premium CSV parsers (Tab 10).

## Security and local files

- **Credentials (Tab 2):** with **Store in OS keychain** (recommended), secrets are written via [keyring](https://github.com/jaraco/keyring) to the system store (e.g. macOS Keychain, Windows Credential Manager, Freedesktop Secret Service). If keychain is off or unavailable, **x_credentials.json** in the repo root holds the same fields in **plain JSON**; it is **gitignored**. The app tries keychain first on load, then the file.
- **Other** local, gitignored data: `my_tweets.json`, `deleted_history.json`, [ai_requests.log](pde/app.py) (AI request debug, no tokens in logs by design), **tos_last_run.json** (ToS run summary and ids), `follows_cache.json` if present. Keep copies private and use tight file permissions. Keychain is not a substitute for a locked full-disk backup policy.

## Fetch vs delete

- Fetching timelines uses the read path (bearer and/or user auth) with Tweepy.
- Deletes use **user auth** (access token + secret) only.

## Development

- **Install dev tools** (with the venv active): `pip install -r requirements-dev.txt`.
- **Tests** — [pyproject.toml](pyproject.toml) sets `testpaths` and `pythonpath`. `pytest tests/ -q` runs:
  - offline [xeraser_analytics](xeraser_analytics.py) parser tests, and
  - a [headless Tk smoke test](tests/test_tk_headless.py) (constructs the main window with no event loop; CI uses [Xvfb](https://en.wikipedia.org/wiki/Xvfb) on Ubuntu).
- **Ruff** (`ruff check` / `ruff format`) and **Mypy** (typed modules under `pde/`, the launcher, and `xeraser_analytics.py`; the large [pde/app.py](pde/app.py) UI is excluded from Ruff in config and Mypy-overridden). `pre-commit install` uses [.pre-commit-config.yaml](.pre-commit-config.yaml).
- **CI** ([.github/workflows/ci.yml](.github/workflows/ci.yml)): Ruff, Mypy, then pytest under `xvfb-run` (Python 3.10, 3.12, 3.13, Ubuntu). No API keys.
- **Dependabot** ([.github/dependabot.yml](.github/dependabot.yml)) proposes monthly updates for pip and GitHub Actions.
- **Optional native packaging** (PyInstaller, etc.): [scripts/packaging_notes.md](scripts/packaging_notes.md). Not required for normal use.
- Design notes: [docs/IMPROVEMENTS_SPEC.md](docs/IMPROVEMENTS_SPEC.md), [docs/TESTS_AND_PATCHES.md](docs/TESTS_AND_PATCHES.md) (some paths may be historical).

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
