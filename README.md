# PleaseDaddyElonNotTheBelt – X Bulk Deleter

A desktop app to bulk delete your X (Twitter) posts, replies, and retweets. Uses the official X API with your own API keys.

## Features

- **Authorization** – Save and test X API credentials (Consumer Key/Secret, Access Token/Secret).
- **My Posts & Replies** – Fetch your tweets, filter by search (plain text or regex), filter by date range, sort newest/oldest, select/deselect for deletion.
- **Deletion Queue** – Preview selected tweets and delete them in bulk (with rate-limit handling).
- **Historical Deletions** – View a running tally and history of deleted tweets (stored locally).

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
   - Set app permissions to **Read + Write + Direct Messages**.
   - **Basic tier** ($100/mo) is required to *fetch* tweet history; free tier can still *delete* tweets (but not list them in-app).

## Usage

```bash
python PleaseDaddyElonNotTheBelt.py
```

1. **Tab 1 – Authorization**: Enter your four API credentials, click **Save Credentials**, then **Test Connection**.
2. **Tab 2 – My Posts & Replies**: Click **Fetch New Tweets** to load your tweets. Use **Search & Select** (optional regex), **Filter & Select** by date (YYYY-MM-DD), or tick checkboxes manually. **Save List** writes the current list to disk.
3. **Tab 3 – Deletion Queue**: Review the list of selected tweets, then click **DELETE ALL SELECTED NOW**. Confirm; the app will delete in the background and respect rate limits.
4. **Tab 4 – Historical Deletions**: See total deleted and a log of past deletions (from local history).

## Local Files

- `x_credentials.json` – Your API credentials (plain text; keep private and out of version control).
- `my_tweets.json` – Cached list of fetched tweets.
- `deleted_history.json` – Record of deleted tweets for the history tab.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md) for dependency attributions.
