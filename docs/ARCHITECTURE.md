# Architecture (local-first)

- **Entry:** [PleaseDaddyElonNotTheBelt.py](../PleaseDaddyElonNotTheBelt.py) runs a dependency check, then `pde.app.main()` which constructs `XBulkDeleter` and the Tk event loop.
- **Layout:** The `pde` package groups paths, constants, AI ToS batching, dependency verification, keychain/file credentials, and atomic JSON I/O. The main window and API/thread logic live in a single large [pde/app.py](../pde/app.py) module for now.
- **Data directory:** [pde/paths.py](../pde/paths.py) `REPO_ROOT` is the repository root. JSON caches (`my_tweets.json`, `deleted_history.json`, `tos_last_run.json`) and optional `x_credentials.json` sit next to the app; the former use rotating `*.bak` files on save via [pde/atomicio.py](../pde/atomicio.py).
- **Threading:** Long work (fetch, ToS, follows, delete batches, analytics) runs in `threading.Thread` targets; the UI is updated with `self.root.after(0, ...)` to stay on the Tk main thread. Never call Tk from worker threads.
- **X / Tweepy:** OAuth user auth is required for your own `get_me` and most write paths. Read paths may use bearer or user auth depending on the method; 401 can trigger a fallback between clients where implemented.
- **Keyring ([pde/secure_creds.py](../pde/secure_creds.py)):** Windows/macOS and Linux (DBus/Secret Service) are supported by the `keyring` project; when it is unavailable, credentials fall back to plain `x_credentials.json` on disk.
- **Offline Tab 10:** [xeraser_analytics.py](../xeraser_analytics.py) parses `tweets.js` and optional Premium CSVs without network I/O; charts use matplotlib inside Tk.

This file is a map for contributors, not a legal or support guarantee.
