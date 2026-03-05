# PleaseDaddyElonNotTheBelt – X Bulk Deleter

A desktop app to bulk delete your X (Twitter) posts, replies, and retweets. Uses the official X API with your own API keys.

## Features

- **Instructions** – Step-by-step guide to get X API keys (Tab 1).
- **Authorization** – Save and test X API credentials; optional **AI Reviewer** (endpoint, model, API token) for natural-language search in Posts & Replies. Token is stored locally and never logged.
- **My Posts & Replies** – Fetch newer/older tweets, import archive, **AI Reviewer** (robot icon) to describe what you’re looking for and apply a suggested filter, and search/filter/sort for queueing.
- **Deletion Queue** – Preview selected tweets and delete them in bulk (with rate-limit handling).
- **Historical Deletions** – View a running tally and history of deleted tweets (stored locally). Per-row actions: **Trash** (remove from history), **Arrow** (open pre-filled compose on X), **Envelope** (edit & post from app).
- **Compose** – Write and post new tweets in-app. Use the Envelope action on a history row to pre-fill from a deleted tweet.

## Requirements

- **Python 3.8+**
- **tweepy** – X API client (`pip install tweepy`)
- **tkinter** – GUI (usually included with Python; on Linux install `python3-tk`)

## Setup

1. Clone or download this repo.
2. Install dependencies:
   ```bash
   pip install tweepy
   ```
   On Linux, also install tkinter, e.g.:
   ```bash
   sudo apt install python3-tk   # Debian/Ubuntu
   sudo dnf install python3-tkinter   # Fedora/RHEL
   sudo pacman -S tk   # Arch
   ```
3. Get X API keys from [developer.x.com](https://developer.x.com):
   - Create a project/app.
   - Copy Consumer Key, Consumer Secret, Access Token, Access Token Secret.
   - (Optional) Copy Bearer token for read-only fetch calls.
   - Set app permissions to **Read + Write + Direct Messages**.
   - **Basic tier** ($100/mo) is required to *fetch* tweet history; free tier can still *delete* tweets (but not list them in-app).

## Usage

```bash
python PleaseDaddyElonNotTheBelt.py
```

1. **Tab 1 – Instructions**: Step-by-step guide to get your X API keys.
2. **Tab 2 – Authorization**: Enter your API credentials, click **Save Credentials**, then **Test User Auth (RW)**. Optionally set **AI Reviewer** (endpoint default: xAI, model dropdown, API token) and save; token is stored in the same local credentials file and is masked in the UI.
3. **Tab 3 – My Posts & Replies**: **Robot icon** opens the AI Reviewer: type what you’re looking for (e.g. “tweets about the weather”), click **Send**; the AI returns a search suggestion and the app applies it to filter the list. Use **Fetch Newer** / **Fetch Older**, **Import Archive**, and Search/Filters to queue items for deletion.
4. **Tab 4 – Deletion Queue**: Review selected tweets, then **DELETE ALL QUEUED NOW** (with confirmation). Unqueue or delete in bulk; batches run in a bottom panel with Pause/Stop.
5. **Tab 5 – Historical Deletions**: View tally and past deletions. Per row: **Trash** (remove from history), **Arrow** (open X intent with pre-filled text), **Envelope** (copy into Compose tab).
6. **Tab 6 – Compose**: Write a tweet (280 chars), **Post** via API or **Clear**. Use **Envelope** on a history row to pre-fill.

### Fetch vs Delete auth behavior

- Fetch uses a read client (Bearer token when available, otherwise user auth).
- The app can retry once with the alternate read auth mode if fetch gets `401 Unauthorized`.
- Delete always uses user-auth credentials (Access Token + Secret) and cannot run with bearer-only auth.

## Local Files

- `x_credentials.json` – Your API credentials (plain text; keep private and out of version control).
- `my_tweets.json` – Cached list of fetched tweets.
- `deleted_history.json` – Record of deleted tweets for the history tab.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for dependency attributions.
