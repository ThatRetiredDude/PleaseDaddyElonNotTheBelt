import sys
import platform
import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import time
import threading
import re
from datetime import datetime

# ────────────────────────────────────────────────
#   DEPENDENCY CHECKER - Runs FIRST
# ────────────────────────────────────────────────

def get_linux_distro():
    try:
        with open("/etc/os-release", encoding="utf-8") as f:
            lines = f.readlines()
        info = {}
        for line in lines:
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                info[key] = value.strip('"')
        return info.get("NAME", "Unknown").lower(), info.get("VERSION_ID", "")
    except OSError:
        return "unknown", ""

def check_dependencies():
    missing = []
    try:
        import tweepy
    except ImportError:
        missing.append("tweepy")
    try:
        import tkinter
    except ImportError:
        missing.append("tkinter")

    if not missing:
        return  # everything is installed

    os_name = platform.system()
    os_release = platform.release()
    python_ver = sys.version.split()[0]

    instr = f"First-time setup — missing dependencies detected\n\n"
    instr += f"OS:      {os_name} {os_release}\n"
    instr += f"Python:  {python_ver}\n\n"
    instr += "Missing packages:\n • " + "\n • ".join(missing) + "\n\n"

    if os_name == "Windows":
        instr += "Run in Command Prompt or PowerShell:\n"
        instr += f"pip install {' '.join(missing)}\n\n"
        instr += "If pip is not found try:\npy -m pip install {' '.join(missing)}\n"
    elif os_name == "Darwin":  # macOS
        instr += "Run in Terminal:\n"
        instr += f"pip3 install {' '.join(missing)}\n\n"
        instr += "If tkinter is missing:\nbrew install python-tk\n"
    elif os_name == "Linux":
        dist_name, dist_ver = get_linux_distro()
        instr += f"Detected Linux: {dist_name.title()} {dist_ver}\n\n"
        instr += "1. Install tkinter (system package):\n"
        if "ubuntu" in dist_name or "debian" in dist_name:
            instr += "sudo apt update && sudo apt install python3-tk\n"
        elif "fedora" in dist_name or "rhel" in dist_name or "centos" in dist_name:
            instr += "sudo dnf install python3-tkinter\n"
        elif "arch" in dist_name or "manjaro" in dist_name:
            instr += "sudo pacman -S tk\n"
        else:
            instr += "Use your distro package manager to install python3-tkinter / tk\n"
        instr += "\n2. Install Python package:\n"
        instr += f"pip3 install --user {' '.join(missing)}\n"
    else:
        instr += f"Manual command:\npip install {' '.join(missing)}\n"

    instr += "\n\nAfter installing, close this window and restart the program."

    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Setup Required - Missing Dependencies", instr)
    root.destroy()
    sys.exit(0)


# Run dependency check immediately
check_dependencies()

# ────────────────────────────────────────────────
#   Now safe to import tweepy and the rest
# ────────────────────────────────────────────────

import tweepy

CREDENTIALS_FILE = "x_credentials.json"
TWEETS_FILE = "my_tweets.json"
HISTORY_FILE = "deleted_history.json"

class XBulkDeleter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PleaseDaddyElonNotTheBelt – X Bulk Deleter")
        self.root.geometry("1100x800")

        self.client = None
        self.tweets = []
        self.deleted_history = []
        self.check_vars = {}
        self.search_var = tk.StringVar()
        self.use_regex_var = tk.BooleanVar(value=False)
        self.from_date_var = tk.StringVar()
        self.to_date_var = tk.StringVar()

        self.create_tabs()
        self.load_credentials()
        self.load_tweets()
        self.load_history()
        self.refresh_tweets_list()
        self.update_delete_preview()
        self.refresh_history_tab()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def create_tabs(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        auth_tab = ttk.Frame(notebook)
        notebook.add(auth_tab, text="1. Authorization")
        self.setup_auth_tab(auth_tab)

        view_tab = ttk.Frame(notebook)
        notebook.add(view_tab, text="2. My Posts & Replies")
        self.setup_view_tab(view_tab)

        del_tab = ttk.Frame(notebook)
        notebook.add(del_tab, text="3. Deletion Queue")
        self.setup_delete_tab(del_tab)

        history_tab = ttk.Frame(notebook)
        notebook.add(history_tab, text="4. Historical Deletions")
        self.setup_history_tab(history_tab)

    def setup_auth_tab(self, parent):
        ttk.Label(parent, text="X API Credentials", font=("Arial", 14, "bold")).pack(pady=(20,10))
        ttk.Label(parent, text="This tool needs YOUR own API keys.\nCreate an app at https://developer.x.com", 
                  justify="left", wraplength=700, foreground="#444").pack(pady=5, padx=30)

        labels = ["Consumer Key (API Key):", "Consumer Secret:", "Access Token:", "Access Token Secret:"]
        self.cred_vars = [tk.StringVar() for _ in range(4)]

        cred_frame = ttk.Frame(parent)
        cred_frame.pack(fill="x", padx=40, pady=15)
        for i, label_text in enumerate(labels):
            ttk.Label(cred_frame, text=label_text, width=25, anchor="e").grid(row=i, column=0, pady=6, sticky="e")
            entry = ttk.Entry(cred_frame, textvariable=self.cred_vars[i], width=55, show="*" if i in (1,3) else None)
            entry.grid(row=i, column=1, pady=6, padx=10, sticky="ew")

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="💾 Save Credentials", command=self.save_credentials).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="🔑 Test Connection", command=self.test_auth).pack(side="left", padx=8)

        instr_frame = ttk.LabelFrame(parent, text=" How to Get Your Keys (Step-by-Step) ", padding=15)
        instr_frame.pack(fill="x", padx=30, pady=15)
        instr_text = tk.Text(instr_frame, height=14, width=85, wrap="word", font=("Arial", 10))
        instr_text.pack(fill="both", expand=True)
        instructions = """1. Go to https://developer.x.com/en/portal/dashboard
2. Log in with the account you want to clean
3. Projects & Apps → + Add App (or create a Project first)
4. Name the app → continue
5. In "Keys and tokens" tab copy these 4 values:
   • Consumer Key (API Key)
   • Consumer Secret
   • Access Token
   • Access Token Secret
6. Set permissions to "Read + Write + Direct Messages"
7. Tier requirement: Basic tier ($100/mo) needed to fetch tweets
   Free tier can only delete (cannot fetch history)

After saving credentials, click "Test Connection" then go to Tab 2."""
        instr_text.insert("1.0", instructions)
        instr_text.config(state="disabled")

    def setup_view_tab(self, parent):
        ctrl_frame = ttk.Frame(parent)
        ctrl_frame.pack(fill="x", pady=8)

        ttk.Button(ctrl_frame, text="🔄 Fetch New Tweets", command=self.fetch_tweets).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="✅ Select All", command=self.select_all).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="❌ Deselect All", command=self.deselect_all).pack(side="left", padx=4)

        ttk.Label(ctrl_frame, text="Search:").pack(side="left", padx=(15,2))
        ttk.Entry(ctrl_frame, textvariable=self.search_var, width=25).pack(side="left", padx=2)
        ttk.Checkbutton(ctrl_frame, text="Use Regex", variable=self.use_regex_var).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="🔍 Search & Select", command=self.search_and_select).pack(side="left", padx=4)

        ttk.Label(ctrl_frame, text="From (YYYY-MM-DD):").pack(side="left", padx=(15,2))
        ttk.Entry(ctrl_frame, textvariable=self.from_date_var, width=12).pack(side="left", padx=2)
        ttk.Label(ctrl_frame, text="To:").pack(side="left", padx=2)
        ttk.Entry(ctrl_frame, textvariable=self.to_date_var, width=12).pack(side="left", padx=2)
        ttk.Button(ctrl_frame, text="📅 Filter & Select", command=self.date_range_select).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="Clear Filter", command=self.clear_date_filter).pack(side="left", padx=2)

        ttk.Button(ctrl_frame, text="⬇️ Sort Newest", command=lambda: self.sort_tweets("newest")).pack(side="left", padx=(20,4))
        ttk.Button(ctrl_frame, text="⬆️ Sort Oldest", command=lambda: self.sort_tweets("oldest")).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="💾 Save List", command=self.save_tweets).pack(side="right", padx=5)

        self.canvas = tk.Canvas(parent, background="#f0f0f0")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0,5))
        scrollbar.pack(side="right", fill="y")

    def setup_delete_tab(self, parent):
        ttk.Label(parent, text="Selected tweets appear here automatically", font=("Arial", 10)).pack(pady=5)
        self.delete_list = tk.Text(parent, height=28, state="disabled", wrap="word", font=("Consolas", 9))
        self.delete_list.pack(fill="both", expand=True, padx=10, pady=5)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=10)
        self.delete_btn = ttk.Button(btn_frame, text="🗑️ DELETE ALL SELECTED NOW", command=self.start_deletion)
        self.delete_btn.pack()

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(parent, textvariable=self.status_var, foreground="blue").pack(pady=5)

    def setup_history_tab(self, parent):
        ttk.Label(parent, text="Deletion History & Running Tally", font=("Arial", 12, "bold")).pack(pady=8)
        self.stats_label = ttk.Label(parent, text="Total deleted: 0 | Original: 0 | Replies: 0 | Retweets: 0", font=("Arial", 10))
        self.stats_label.pack(pady=5)
        ttk.Label(parent, text="Past deletions (newest first):").pack(anchor="w", padx=10)
        self.history_text = tk.Text(parent, height=25, state="disabled", wrap="word", font=("Consolas", 9))
        self.history_text.pack(fill="both", expand=True, padx=10, pady=5)

    # ====================== CREDENTIALS ======================
    def load_credentials(self):
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, encoding="utf-8") as f:
                    creds = json.load(f)
                for var, key in zip(self.cred_vars, ["consumer_key", "consumer_secret", "access_token", "access_token_secret"]):
                    var.set(creds.get(key, ""))
                self.init_client()
            except (json.JSONDecodeError, OSError, KeyError):
                pass

    def save_credentials(self):
        creds = {
            "consumer_key": self.cred_vars[0].get().strip(),
            "consumer_secret": self.cred_vars[1].get().strip(),
            "access_token": self.cred_vars[2].get().strip(),
            "access_token_secret": self.cred_vars[3].get().strip(),
        }
        with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2)
        messagebox.showinfo("Saved", "Credentials saved locally.")
        self.init_client()

    def init_client(self):
        try:
            self.client = tweepy.Client(
                consumer_key=self.cred_vars[0].get().strip(),
                consumer_secret=self.cred_vars[1].get().strip(),
                access_token=self.cred_vars[2].get().strip(),
                access_token_secret=self.cred_vars[3].get().strip(),
                wait_on_rate_limit=True
            )
        except Exception:
            self.client = None

    def test_auth(self):
        if not self.client:
            self.init_client()
        if not self.client:
            messagebox.showerror("Error", "No credentials loaded")
            return
        try:
            me = self.client.get_me(user_fields=["username"])
            messagebox.showinfo("Success", f"Logged in as @{me.data.username}")
        except Exception as e:
            messagebox.showerror("Auth Failed", str(e))

    # ====================== PERSISTENCE ======================
    def load_tweets(self):
        if os.path.exists(TWEETS_FILE):
            try:
                with open(TWEETS_FILE, encoding="utf-8") as f:
                    self.tweets = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.tweets = []

    def save_tweets(self):
        tmp = TWEETS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.tweets, f, indent=2)
        os.replace(tmp, TWEETS_FILE)

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, encoding="utf-8") as f:
                    self.deleted_history = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.deleted_history = []

    def save_history(self):
        tmp = HISTORY_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.deleted_history, f, indent=2)
        os.replace(tmp, HISTORY_FILE)

    def on_close(self):
        self.save_tweets()
        self.save_history()
        self.root.destroy()

    # ====================== FETCH ======================
    def fetch_tweets(self):
        if not self.client:
            messagebox.showerror("Error", "Please set up credentials first (Tab 1)")
            return
        self.status_var.set("Fetching new tweets...")
        self.root.update()
        try:
            user = self.client.get_me()
            user_id = user.data.id
            since_id = str(max((int(t["id"]) for t in self.tweets), default=0)) if self.tweets else None
            all_new = []
            pagination_token = None
            while True:
                response = self.client.get_users_tweets(
                    id=user_id, max_results=100, pagination_token=pagination_token,
                    since_id=since_id, tweet_fields=["created_at", "referenced_tweets", "in_reply_to_user_id", "text"]
                )
                if not response.data:
                    break
                for t in response.data:
                    tweet_type = "original"
                    if t.referenced_tweets:
                        for ref in t.referenced_tweets:
                            if ref.type == "retweeted":
                                tweet_type = "retweet"
                                break
                            elif ref.type == "replied_to":
                                tweet_type = "reply"
                                break
                    elif getattr(t, "in_reply_to_user_id", None):
                        tweet_type = "reply"
                    all_new.append({
                        "id": str(t.id),
                        "text": (t.text or "")[:280],
                        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M") if t.created_at else "N/A",
                        "type": tweet_type,
                        "selected": False
                    })
                if "next_token" not in response.meta:
                    break
                pagination_token = response.meta["next_token"]
                time.sleep(1.1)
            existing = {t["id"] for t in self.tweets}
            added = 0
            for nt in all_new:
                if nt["id"] not in existing:
                    self.tweets.append(nt)
                    added += 1
            self.tweets.sort(key=lambda x: x["created_at"], reverse=True)
            self.save_tweets()
            self.refresh_tweets_list()
            self.update_delete_preview()
            messagebox.showinfo("Done", f"Added {added} new tweet(s). Total now: {len(self.tweets)}")
        except Exception as e:
            messagebox.showerror("Fetch Error", str(e))
        finally:
            self.status_var.set("Ready")

    # ====================== SEARCH (Regex supported) ======================
    def search_and_select(self):
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Empty", "Enter words or regex")
            return
        keywords = [w.strip() for w in query.split(",") if w.strip()]
        if self.use_regex_var.get():
            try:
                for pat in keywords:
                    re.compile(pat)
            except re.error:
                messagebox.showerror("Regex Error", "Invalid regex pattern. Fix it before selecting.")
                return
        count = 0
        for tweet in self.tweets:
            text = tweet.get("text") or ""
            match = False
            if self.use_regex_var.get():
                match = any(re.search(pat, text, re.IGNORECASE) for pat in keywords)
            else:
                match = any(kw.lower() in text.lower() for kw in keywords)
            if match:
                tweet["selected"] = True
                count += 1
        self.refresh_tweets_list()
        self.update_delete_preview()
        messagebox.showinfo("Search Done", f"Auto-selected {count} tweet(s).")

    # ====================== DATE FILTER ======================
    def date_range_select(self):
        from_str = self.from_date_var.get().strip()
        to_str = self.to_date_var.get().strip()
        try:
            from_dt = datetime.strptime(from_str, "%Y-%m-%d") if from_str else datetime.min
            to_dt = datetime.strptime(to_str, "%Y-%m-%d") if to_str else datetime.max
        except ValueError:
            messagebox.showerror("Date Error", "Use YYYY-MM-DD format")
            return
        count = 0
        for tweet in self.tweets:
            try:
                created = tweet.get("created_at", "")[:10]
                tweet_dt = datetime.strptime(created, "%Y-%m-%d")
                if from_dt <= tweet_dt <= to_dt:
                    tweet["selected"] = True
                    count += 1
            except (ValueError, KeyError):
                pass
        self.refresh_tweets_list()
        self.update_delete_preview()
        messagebox.showinfo("Date Filter", f"Selected {count} tweets in range.")

    def clear_date_filter(self):
        self.from_date_var.set("")
        self.to_date_var.set("")

    # ====================== SORT ======================
    def sort_tweets(self, order):
        reverse = order == "newest"
        self.tweets.sort(key=lambda x: x["created_at"], reverse=reverse)
        self.refresh_tweets_list()
        self.update_delete_preview()

    # ====================== LIST DISPLAY ======================
    def refresh_tweets_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()
        colors = {"original": "#d4edda", "reply": "#cce5ff", "retweet": "#fff3cd"}
        for tweet in self.tweets:
            var = tk.BooleanVar(value=tweet.get("selected", False))
            self.check_vars[tweet["id"]] = var
            row = tk.Frame(self.scroll_frame, bg=colors.get(tweet["type"], "#f8f9fa"))
            row.pack(fill="x", padx=5, pady=2)
            chk = tk.Checkbutton(row, variable=var, bg=colors.get(tweet["type"], "#f8f9fa"),
                                 command=lambda t=tweet, v=var: self.on_check_toggle(t, v))
            chk.pack(side="left", padx=5)
            text = tweet.get("text") or ""
            txt = f"{tweet['created_at']} | {tweet['type'].upper():7} | {text[:110]}{'...' if len(text) > 110 else ''}"
            tk.Label(row, text=txt, anchor="w", bg=colors.get(tweet["type"], "#f8f9fa"), justify="left", wraplength=850).pack(side="left", fill="x", padx=5)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_check_toggle(self, tweet, var):
        tweet["selected"] = var.get()
        self.update_delete_preview()

    def select_all(self):
        for t in self.tweets:
            t["selected"] = True
        self.refresh_tweets_list()
        self.update_delete_preview()

    def deselect_all(self):
        for t in self.tweets:
            t["selected"] = False
        self.refresh_tweets_list()
        self.update_delete_preview()

    def update_delete_preview(self):
        selected = [t for t in self.tweets if t["selected"]]
        self.delete_list.config(state="normal")
        self.delete_list.delete("1.0", tk.END)
        if not selected:
            self.delete_list.insert("1.0", "No tweets selected yet.")
        else:
            for t in selected[:250]:
                self.delete_list.insert("end", f"✓ {t['created_at']} | {t['type']} | {(t.get('text') or '')[:75]}\n")
            if len(selected) > 250:
                self.delete_list.insert("end", f"\n... and {len(selected)-250} more")
        self.delete_list.config(state="disabled")

    # ====================== DELETION ======================
    def start_deletion(self):
        selected = [t for t in self.tweets if t["selected"]]
        if not selected:
            messagebox.showwarning("Nothing selected", "Select tweets in Tab 2 first.")
            return
        if not messagebox.askyesno("Confirm", f"PERMANENTLY delete {len(selected)} tweets?\nThis cannot be undone."):
            return
        self.delete_btn.config(state="disabled")
        threading.Thread(target=self.delete_thread, args=(selected,), daemon=True).start()

    def _apply_single_deletion(self, tweet_id, history_entry):
        """Run on main thread: update tweets and history lists."""
        self.tweets = [t for t in self.tweets if t["id"] != tweet_id]
        self.deleted_history.insert(0, history_entry)

    def delete_thread(self, selected):
        deleted_count = 0
        try:
            for i, tweet in enumerate(selected):
                try:
                    self.client.delete_tweet(tweet["id"])
                    deleted_count += 1
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    hist_entry = {**tweet, "deleted_at": now}
                    self.root.after(0, lambda tid=tweet["id"], he=hist_entry: self._apply_single_deletion(tid, he))
                    self.root.after(0, lambda c=deleted_count, total=len(selected): self.status_var.set(f"Deleted {c}/{total}"))
                    if (i + 1) % 50 == 0:
                        self.root.after(0, lambda: messagebox.showinfo("Rate Limit", "Waiting 15 minutes for API..."))
                        time.sleep(901)
                    time.sleep(0.6)
                except tweepy.TooManyRequests:
                    self.root.after(0, lambda: messagebox.showinfo("Rate Limit", "Waiting 15 minutes..."))
                    time.sleep(901)
                except Exception as e:
                    self.root.after(0, lambda err=str(e): self.status_var.set(f"Error: {err}"))
                    time.sleep(2)
            self.root.after(0, self._finish_deletion)
            self.root.after(0, lambda: messagebox.showinfo("Finished", f"Successfully deleted {deleted_count} tweets!"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, lambda: self.delete_btn.config(state="normal"))
            self.root.after(0, lambda: self.status_var.set("Ready"))

    def _finish_deletion(self):
        """Run on main thread: persist and refresh UI after deletion run."""
        self.save_tweets()
        self.save_history()
        self.refresh_tweets_list()
        self.update_delete_preview()
        self.refresh_history_tab()

    # ====================== HISTORY ======================
    def refresh_history_tab(self):
        total = len(self.deleted_history)
        by_type = {"original": 0, "reply": 0, "retweet": 0}
        for h in self.deleted_history:
            by_type[h.get("type", "original")] += 1
        self.stats_label.config(text=f"Total deleted: {total} | Original: {by_type['original']} | Replies: {by_type['reply']} | Retweets: {by_type['retweet']}")
        self.history_text.config(state="normal")
        self.history_text.delete("1.0", tk.END)
        if not self.deleted_history:
            self.history_text.insert("1.0", "No deletions yet.")
        else:
            for h in self.deleted_history[:300]:
                self.history_text.insert("end", f"🗑️ {h['deleted_at']} | {h['created_at']} | {h['type'].upper()} | {(h.get('text') or '')[:90]}\n")
            if len(self.deleted_history) > 300:
                self.history_text.insert("end", f"\n... and {len(self.deleted_history)-300} more")
        self.history_text.config(state="disabled")

if __name__ == "__main__":
    print("Starting PleaseDaddyElonNotTheBelt.py")
    print("Dependency check passed.")
    XBulkDeleter()