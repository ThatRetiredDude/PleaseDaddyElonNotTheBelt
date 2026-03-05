import sys
import platform
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
import time
import threading
import re
import unicodedata
import webbrowser
from datetime import datetime
from urllib.parse import quote
from urllib.request import Request, urlopen
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# AI request debug logger (writes to ai_requests.log, never logs tokens)
_ai_logger = logging.getLogger("PleaseDaddyElonNotTheBelt.ai")
_ai_logger.setLevel(logging.DEBUG)
if not _ai_logger.handlers:
    _fh = logging.FileHandler(os.path.join(BASE_DIR, "ai_requests.log"), encoding="utf-8")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    _ai_logger.addHandler(_fh)

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

CREDENTIALS_FILE = os.path.join(BASE_DIR, "x_credentials.json")
TWEETS_FILE = os.path.join(BASE_DIR, "my_tweets.json")
HISTORY_FILE = os.path.join(BASE_DIR, "deleted_history.json")
CHUNK_SIZE = 80
AI_ENDPOINT_DEFAULT = "https://api.x.ai/v1"
AI_REQUEST_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# Top models; model -> default API endpoint (OpenAI-compatible where applicable)
AI_MODELS = [
    # Gemini 3.1+ (latest)
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-3-flash-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    # OpenAI 5.x (latest)
    "gpt-5.2",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-5-chat-latest",
    "gpt-5-main",
    "gpt-5-main-mini",
    "gpt-5-thinking",
    "gpt-5-thinking-mini",
    "gpt-5-thinking-nano",
    "gpt-5-thinking-pro",
    # Claude 4.6+ (latest)
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
    # xAI Grok
    "grok-2",
    "grok-2-vision",
    "grok-2-latest",
    "grok-3",
    "grok-3-mini",
    "grok-4-fast-reasoning",
    "grok-4-fast-non-reasoning",
    "grok-4-1-fast-reasoning",
    "grok-4-1-fast-non-reasoning",
    "grok-4-0709",
    "grok-code-fast-1",
    # OpenAI 4.x / o1
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo",
    "o1",
    "o1-mini",
    # Claude 3.x
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    # Gemini 1.5 / 1.0
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
    "llama-3.3-70b-instruct",
    "llama-3.2-90b-instruct",
    "llama-3.1-70b-instruct",
    "llama-3.1-8b-instruct",
    "llama-3.1-405b-instruct",
    "mixtral-8x7b-instruct",
    "mistral-large-latest",
    "mistral-medium-latest",
    "mistral-small-latest",
    "deepseek-chat",
    "deepseek-coder",
    "qwen-2.5-72b-instruct",
    "codellama-70b-instruct",
    "command-r-plus",
]
# Default endpoint per model (used when user picks from list to auto-fill endpoint)
AI_MODEL_DEFAULT_ENDPOINT = {
    # Gemini 3.1+
    "gemini-3.1-pro-preview": "https://generativelanguage.googleapis.com/v1beta",
    "gemini-3.1-flash-lite-preview": "https://generativelanguage.googleapis.com/v1beta",
    "gemini-3-flash-preview": "https://generativelanguage.googleapis.com/v1beta",
    "gemini-2.5-pro": "https://generativelanguage.googleapis.com/v1beta",
    "gemini-2.5-flash": "https://generativelanguage.googleapis.com/v1beta",
    "gemini-2.5-flash-lite": "https://generativelanguage.googleapis.com/v1beta",
    # OpenAI 5.x
    "gpt-5.2": "https://api.openai.com/v1",
    "gpt-5": "https://api.openai.com/v1",
    "gpt-5-mini": "https://api.openai.com/v1",
    "gpt-5-nano": "https://api.openai.com/v1",
    "gpt-5-chat-latest": "https://api.openai.com/v1",
    "gpt-5-main": "https://api.openai.com/v1",
    "gpt-5-main-mini": "https://api.openai.com/v1",
    "gpt-5-thinking": "https://api.openai.com/v1",
    "gpt-5-thinking-mini": "https://api.openai.com/v1",
    "gpt-5-thinking-nano": "https://api.openai.com/v1",
    "gpt-5-thinking-pro": "https://api.openai.com/v1",
    # Claude 4.6+
    "claude-opus-4-6": "https://api.anthropic.com/v1",
    "claude-sonnet-4-6": "https://api.anthropic.com/v1",
    "claude-haiku-4-5": "https://api.anthropic.com/v1",
    # xAI Grok
    "grok-2": "https://api.x.ai/v1",
    "grok-2-vision": "https://api.x.ai/v1",
    "grok-2-latest": "https://api.x.ai/v1",
    "grok-3": "https://api.x.ai/v1",
    "grok-3-mini": "https://api.x.ai/v1",
    "grok-4-fast-reasoning": "https://api.x.ai/v1",
    "grok-4-fast-non-reasoning": "https://api.x.ai/v1",
    "grok-4-1-fast-reasoning": "https://api.x.ai/v1",
    "grok-4-1-fast-non-reasoning": "https://api.x.ai/v1",
    "grok-4-0709": "https://api.x.ai/v1",
    "grok-code-fast-1": "https://api.x.ai/v1",
    # OpenAI 4.x / o1
    "gpt-4o": "https://api.openai.com/v1",
    "gpt-4o-mini": "https://api.openai.com/v1",
    "gpt-4-turbo": "https://api.openai.com/v1",
    "gpt-4": "https://api.openai.com/v1",
    "gpt-3.5-turbo": "https://api.openai.com/v1",
    "o1": "https://api.openai.com/v1",
    "o1-mini": "https://api.openai.com/v1",
    # Claude 3.x
    "claude-3-5-sonnet-20241022": "https://api.anthropic.com/v1",
    "claude-3-5-haiku-20241022": "https://api.anthropic.com/v1",
    "claude-3-opus-20240229": "https://api.anthropic.com/v1",
    "claude-3-sonnet-20240229": "https://api.anthropic.com/v1",
    "claude-3-haiku-20240307": "https://api.anthropic.com/v1",
    # Gemini 1.5 / 1.0
    "gemini-1.5-pro": "https://generativelanguage.googleapis.com/v1beta",
    "gemini-1.5-flash": "https://generativelanguage.googleapis.com/v1beta",
    "gemini-1.0-pro": "https://generativelanguage.googleapis.com/v1beta",
    "llama-3.3-70b-instruct": "https://api.groq.com/openai/v1",
    "llama-3.2-90b-instruct": "https://api.groq.com/openai/v1",
    "llama-3.1-70b-instruct": "https://api.groq.com/openai/v1",
    "llama-3.1-8b-instruct": "https://api.groq.com/openai/v1",
    "llama-3.1-405b-instruct": "https://api.groq.com/openai/v1",
    "mixtral-8x7b-instruct": "https://api.groq.com/openai/v1",
    "mistral-large-latest": "https://api.mistral.ai/v1",
    "mistral-medium-latest": "https://api.mistral.ai/v1",
    "mistral-small-latest": "https://api.mistral.ai/v1",
    "deepseek-chat": "https://api.deepseek.com/v1",
    "deepseek-coder": "https://api.deepseek.com/v1",
    "qwen-2.5-72b-instruct": "https://api.together.xyz/v1",
    "codellama-70b-instruct": "https://api.together.xyz/v1",
    "command-r-plus": "https://api.cohere.ai/v1",
}
# Max context window (tokens) per model for AI Scrub batching; unknown models use AI_CONTEXT_FALLBACK_TOKENS
AI_MODEL_CONTEXT_TOKENS = {
    "gemini-3.1-pro-preview": 1_000_000,
    "gemini-3.1-flash-lite-preview": 1_000_000,
    "gemini-3-flash-preview": 1_000_000,
    "gemini-2.5-pro": 256_000,
    "gemini-2.5-flash": 256_000,
    "gemini-2.5-flash-lite": 256_000,
    "gpt-5.2": 128_000,
    "gpt-5": 128_000,
    "gpt-5-mini": 128_000,
    "gpt-5-nano": 128_000,
    "gpt-5-chat-latest": 128_000,
    "gpt-5-main": 128_000,
    "gpt-5-main-mini": 128_000,
    "gpt-5-thinking": 128_000,
    "gpt-5-thinking-mini": 128_000,
    "gpt-5-thinking-nano": 128_000,
    "gpt-5-thinking-pro": 128_000,
    "claude-opus-4-6": 200_000,
    "claude-sonnet-4-6": 200_000,
    "claude-haiku-4-5": 200_000,
    "grok-2": 131_072,
    "grok-2-vision": 131_072,
    "grok-2-latest": 131_072,
    "grok-3": 131_072,
    "grok-3-mini": 131_072,
    "grok-4-fast-reasoning": 262_144,
    "grok-4-fast-non-reasoning": 262_144,
    "grok-4-1-fast-reasoning": 2_000_000,
    "grok-4-1-fast-non-reasoning": 2_000_000,
    "grok-4-0709": 262_144,
    "grok-code-fast-1": 256_000,
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "gpt-4-turbo": 128_000,
    "gpt-4": 128_000,
    "gpt-3.5-turbo": 16_385,
    "o1": 128_000,
    "o1-mini": 128_000,
    "claude-3-5-sonnet-20241022": 200_000,
    "claude-3-5-haiku-20241022": 200_000,
    "claude-3-opus-20240229": 200_000,
    "claude-3-sonnet-20240229": 200_000,
    "claude-3-haiku-20240307": 200_000,
    "gemini-1.5-pro": 128_000,
    "gemini-1.5-flash": 128_000,
    "gemini-1.0-pro": 32_000,
    "llama-3.3-70b-instruct": 128_000,
    "llama-3.2-90b-instruct": 128_000,
    "llama-3.1-70b-instruct": 128_000,
    "llama-3.1-8b-instruct": 128_000,
    "llama-3.1-405b-instruct": 128_000,
    "mixtral-8x7b-instruct": 32_000,
    "mistral-large-latest": 128_000,
    "mistral-medium-latest": 32_000,
    "mistral-small-latest": 32_000,
    "deepseek-chat": 128_000,
    "deepseek-coder": 128_000,
    "qwen-2.5-72b-instruct": 32_000,
    "codellama-70b-instruct": 32_000,
    "command-r-plus": 128_000,
}
AI_CONTEXT_FALLBACK_TOKENS = 32_000
CHARS_PER_TOKEN = 3
TWEET_OVERHEAD_CHARS = 20
AI_RESERVED_TOKENS = 3000
AI_CONTEXT_SAFETY_FACTOR = 0.9


def get_model_context_tokens(model_id):
    """Return max context tokens for model; fallback for unknown models."""
    return AI_MODEL_CONTEXT_TOKENS.get((model_id or "").strip(), AI_CONTEXT_FALLBACK_TOKENS)


def estimate_tokens_for_tweet(tweet):
    """Conservative token estimate from tweet text (chars/3 + overhead)."""
    text = (tweet.get("text") or "")
    return max(1, (len(text) + TWEET_OVERHEAD_CHARS) // CHARS_PER_TOKEN)


def get_batch_token_budget(model_id):
    """Input token budget for one batch (90% of context minus reserved)."""
    ctx = get_model_context_tokens(model_id)
    return max(500, int(ctx * AI_CONTEXT_SAFETY_FACTOR) - AI_RESERVED_TOKENS)


def build_ai_batches(tweets, model_id):
    """Split tweets into batches that fit within model context. Yields list of tweet lists."""
    budget = get_batch_token_budget(model_id)
    batch = []
    used = 0
    for t in tweets:
        need = estimate_tokens_for_tweet(t)
        if batch and used + need > budget:
            yield batch
            batch = []
            used = 0
        batch.append(t)
        used += need
    if batch:
        yield batch


class XBulkDeleter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PleaseDaddyElonNotTheBelt – X Bulk Deleter")
        self.root.geometry("1100x800")
        self.theme = {
            "window_bg": "#0f1419",
            "panel_bg": "#161b22",
            "panel_alt": "#1f2630",
            "border": "#30363d",
            "text": "#e6edf3",
            "muted_text": "#9da7b3",
            "accent": "#58a6ff",
            "input_bg": "#0d1117",
            "input_fg": "#e6edf3",
            "input_border": "#3d444d",
            "tweet_original_bg": "#243b2f",
            "tweet_reply_bg": "#23374d",
            "tweet_retweet_bg": "#4a3d1f",
        }
        self.root.configure(bg=self.theme["window_bg"])

        self.client = None
        self.user_client = None
        self.bearer_client = None
        self.read_client = None
        self.tweets = []
        self.deleted_history = []
        self.check_vars = {}
        self.queue_vars = {}
        self.search_var = tk.StringVar()
        self.search_filter_query = ""
        self.search_filter_regex = False
        self.use_regex_var = tk.BooleanVar(value=True)
        self.from_date_var = tk.StringVar()
        self.to_date_var = tk.StringVar()
        self.type_filter_var = tk.StringVar(value="all")
        self.date_sort_var = tk.StringVar(value="newest")
        self._tweet_wheel_bound = False
        self.batch_counter = 0
        self.active_batch = None
        self.pending_batches = []
        self.batch_pause_event = threading.Event()
        self.batch_pause_event.set()
        self.batch_stop_requested = False
        self._display_tweets_cache = []
        self._tweets_rendered_count = 0
        self._queue_display_cache = []
        self._queue_rendered_count = 0
        self._history_rendered_count = 0
        self._queue_wheel_bound = False
        self._history_wheel_bound = False
        self._tooltip_after_id = None
        self._tooltip_win = None

        self.setup_theme()
        self.create_tabs()
        self.load_credentials()
        self.load_tweets()
        self.load_history()
        self.refresh_tweets_list()
        self.update_delete_preview()
        self.refresh_history_tab()
        self._refresh_ai_scrub_coverage_preview()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def setup_theme(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=self.theme["panel_bg"], foreground=self.theme["text"])
        style.configure("TFrame", background=self.theme["panel_bg"])
        style.configure("TLabel", background=self.theme["panel_bg"], foreground=self.theme["text"])
        style.configure("Title.TLabel", background=self.theme["panel_bg"], foreground=self.theme["text"])
        style.configure("Muted.TLabel", background=self.theme["panel_bg"], foreground=self.theme["muted_text"])
        style.configure("Status.TLabel", background=self.theme["panel_bg"], foreground=self.theme["accent"])
        style.configure("TButton", background=self.theme["panel_alt"], foreground=self.theme["text"])
        style.map(
            "TButton",
            background=[("active", "#273142"), ("pressed", "#1b2433")],
            foreground=[("disabled", self.theme["muted_text"]), ("active", self.theme["text"])]
        )
        style.configure(
            "TEntry",
            fieldbackground=self.theme["input_bg"],
            foreground=self.theme["input_fg"]
        )
        style.map("TEntry", fieldbackground=[("disabled", "#2a2f36")], foreground=[("disabled", self.theme["muted_text"])])
        style.configure("TCheckbutton", background=self.theme["panel_bg"], foreground=self.theme["text"])
        style.map("TCheckbutton", background=[("active", self.theme["panel_bg"])], foreground=[("active", self.theme["text"])])
        style.configure("TLabelframe", background=self.theme["panel_bg"], bordercolor=self.theme["border"])
        style.configure("TLabelframe.Label", background=self.theme["panel_bg"], foreground=self.theme["text"])
        style.configure("Vertical.TScrollbar", background=self.theme["panel_alt"], troughcolor=self.theme["panel_bg"])
        style.configure("TNotebook", background=self.theme["window_bg"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=self.theme["panel_alt"],
            foreground=self.theme["muted_text"]
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.theme["panel_bg"]), ("active", "#2a3340")],
            foreground=[("selected", self.theme["text"]), ("active", self.theme["text"])]
        )
        style.configure(
            "DangerDelete.TButton",
            background="#ff4d4d",
            foreground="#000000",
            font=("Arial", 10, "bold")
        )
        style.map(
            "DangerDelete.TButton",
            background=[("active", "#ff6666"), ("pressed", "#e64545")],
            foreground=[("active", "#000000"), ("pressed", "#000000")]
        )
        style.configure(
            "Unqueue.TButton",
            background="#2ea043",
            foreground="#ffffff",
            font=("Arial", 10, "bold")
        )
        style.map(
            "Unqueue.TButton",
            background=[("active", "#3fb950"), ("pressed", "#238636")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")]
        )

    def _style_text_widget(self, widget):
        widget.configure(
            bg=self.theme["input_bg"],
            fg=self.theme["text"],
            insertbackground=self.theme["text"],
            selectbackground="#2f81f7",
            selectforeground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.theme["border"],
            highlightcolor=self.theme["accent"]
        )

    def create_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        instr_tab = ttk.Frame(self.notebook)
        self.notebook.add(instr_tab, text="1. Instructions")
        self.setup_instructions_tab(instr_tab)

        auth_tab = ttk.Frame(self.notebook)
        self.notebook.add(auth_tab, text="2. Authorization")
        self.setup_auth_tab(auth_tab)

        view_tab = ttk.Frame(self.notebook)
        self.notebook.add(view_tab, text="3. My Posts & Replies")
        self.setup_view_tab(view_tab)

        del_tab = ttk.Frame(self.notebook)
        self.notebook.add(del_tab, text="4. Deletion Queue")
        self.setup_delete_tab(del_tab)

        history_tab = ttk.Frame(self.notebook)
        self.notebook.add(history_tab, text="5. Historical Deletions")
        self.setup_history_tab(history_tab)

        compose_tab = ttk.Frame(self.notebook)
        self.notebook.add(compose_tab, text="6. Compose")
        self.setup_compose_tab(compose_tab)

        ai_scrub_tab = ttk.Frame(self.notebook)
        self.notebook.add(ai_scrub_tab, text="7. AI Scrub")
        self.ai_scrub_tab_index = 6
        self.setup_ai_scrub_tab(ai_scrub_tab)

    def setup_instructions_tab(self, parent):
        ttk.Label(parent, text="How to Get Your Keys (Step-by-Step)", font=("Arial", 14, "bold"), style="Title.TLabel").pack(pady=(20,10))
        instr_frame = ttk.LabelFrame(parent, text=" Setup ", padding=15)
        instr_frame.pack(fill="both", expand=True, padx=30, pady=15)
        instr_text = tk.Text(instr_frame, height=20, width=85, wrap="word", font=("Arial", 10))
        self._style_text_widget(instr_text)
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

After saving credentials (Tab 2 – Authorization):
• "Test User Auth (RW)" validates Consumer/Access tokens
• "Test Bearer (RO)" validates Bearer token for read-only endpoints
Then go to Tab 3 – My Posts & Replies."""
        instr_text.insert("1.0", instructions)
        instr_text.config(state="disabled")

    def setup_auth_tab(self, parent):
        ttk.Label(parent, text="X API Credentials", font=("Arial", 14, "bold"), style="Title.TLabel").pack(pady=(20,10))
        ttk.Label(parent, text="This tool needs YOUR own API keys. Create an app at https://developer.x.com (see Tab 1 for steps).",
                  justify="left", wraplength=700, style="Muted.TLabel").pack(pady=5, padx=30)

        labels = [
            "Consumer Key (API Key):",
            "Consumer Secret:",
            "Access Token:",
            "Access Token Secret:",
            "Bearer Token (read-only, optional):"
        ]
        self.cred_vars = [tk.StringVar() for _ in range(5)]

        cred_frame = ttk.Frame(parent)
        cred_frame.pack(fill="x", padx=40, pady=15)
        for i, label_text in enumerate(labels):
            ttk.Label(cred_frame, text=label_text, width=25, anchor="e").grid(row=i, column=0, pady=6, sticky="e")
            entry = ttk.Entry(cred_frame, textvariable=self.cred_vars[i], width=55, show="*" if i in (1, 3) else None)
            entry.grid(row=i, column=1, pady=6, padx=10, sticky="ew")

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="💾 Save Credentials", command=self.save_credentials).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="🔑 Test User Auth (RW)", command=self.test_auth).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="🧪 Test Bearer (RO)", command=self.test_bearer_auth).pack(side="left", padx=8)

        # AI Reviewer section (model first, then endpoint so selection can auto-fill endpoint)
        ai_frame = ttk.LabelFrame(parent, text=" AI Reviewer (optional) ", padding=15)
        ai_frame.pack(fill="x", padx=30, pady=15)
        ttk.Label(ai_frame, text="Use the robot icon in Posts & Replies to ask AI to help filter tweets. Token is stored locally and never logged. Model and endpoint are typeable; pick from the list or enter a custom model/endpoint.",
                 style="Muted.TLabel", wraplength=600).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(ai_frame, text="Model:", width=18, anchor="e").grid(row=1, column=0, pady=4, sticky="e")
        self.ai_model_var = tk.StringVar(value=AI_MODELS[0] if AI_MODELS else "")
        default_endpoint = AI_MODEL_DEFAULT_ENDPOINT.get(AI_MODELS[0], AI_ENDPOINT_DEFAULT) if AI_MODELS else AI_ENDPOINT_DEFAULT
        self.ai_endpoint_var = tk.StringVar(value=default_endpoint)
        model_combo = ttk.Combobox(ai_frame, textvariable=self.ai_model_var, values=AI_MODELS, width=48)
        model_combo.grid(row=1, column=1, pady=4, padx=8, sticky="ew")
        model_combo.bind("<<ComboboxSelected>>", self._on_ai_model_selected)
        ttk.Label(ai_frame, text="AI endpoint:", width=18, anchor="e").grid(row=2, column=0, pady=4, sticky="e")
        ttk.Entry(ai_frame, textvariable=self.ai_endpoint_var, width=50).grid(row=2, column=1, pady=4, padx=8, sticky="ew")
        ttk.Label(ai_frame, text="API token:", width=18, anchor="e").grid(row=3, column=0, pady=4, sticky="e")
        self.ai_token_var = tk.StringVar()
        ai_token_entry = ttk.Entry(ai_frame, textvariable=self.ai_token_var, width=50, show="*")
        ai_token_entry.grid(row=3, column=1, pady=4, padx=8, sticky="ew")
        ai_frame.columnconfigure(1, weight=1)

    def _on_ai_model_selected(self, event=None):
        """When user picks a model from the list, auto-fill the endpoint only if it's empty or still a known default (so custom endpoints are not overwritten)."""
        model = (self.ai_model_var.get() or "").strip()
        if not model or model not in AI_MODEL_DEFAULT_ENDPOINT:
            return
        current = (self.ai_endpoint_var.get() or "").strip()
        known_endpoints = set(AI_MODEL_DEFAULT_ENDPOINT.values())
        if current and current.rstrip("/") not in {e.rstrip("/") for e in known_endpoints}:
            return  # user has typed a custom endpoint; don't overwrite
        self.ai_endpoint_var.set(AI_MODEL_DEFAULT_ENDPOINT[model])

    def setup_view_tab(self, parent):
        ctrl_frame = ttk.Frame(parent)
        ctrl_frame.pack(fill="x", pady=(8, 4))

        ttk.Button(ctrl_frame, text="🤖", width=3, command=lambda: self.notebook.select(self.ai_scrub_tab_index)).pack(side="left", padx=2)
        ttk.Button(ctrl_frame, text="🔄 Fetch Newer", command=lambda: self.fetch_tweets("newer")).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="⏮️ Fetch Older", command=lambda: self.fetch_tweets("older")).pack(side="left", padx=4)
        ttk.Button(ctrl_frame, text="📥 Import Archive", command=self.import_archive_tweets).pack(side="left", padx=4)

        ttk.Label(ctrl_frame, text="Search:").pack(side="left", padx=(12, 2))
        ttk.Entry(ctrl_frame, textvariable=self.search_var, width=26).pack(side="left", padx=2)
        ttk.Button(ctrl_frame, text="🔍 Search / Filter", command=self.search_and_select).pack(side="left", padx=4)

        self.advanced_btn_text = tk.StringVar(value="Advanced ▾")
        ttk.Button(ctrl_frame, textvariable=self.advanced_btn_text, command=self.toggle_advanced_controls).pack(side="left", padx=8)
        ttk.Button(ctrl_frame, text="💾 Save List", command=self.save_tweets).pack(side="right", padx=5)

        self.advanced_ctrl_frame = ttk.Frame(parent)
        self.advanced_visible = True
        self.advanced_ctrl_frame.pack(fill="x", pady=(0, 8))

        row1 = ttk.Frame(self.advanced_ctrl_frame)
        row1.pack(fill="x", pady=2)
        ttk.Checkbutton(row1, text="Use Regex", variable=self.use_regex_var).pack(side="left", padx=4)
        ttk.Button(row1, text="✅ Select All", command=self.select_all).pack(side="left", padx=4)
        ttk.Button(row1, text="❌ Deselect All", command=self.deselect_all).pack(side="left", padx=4)

        row2 = ttk.Frame(self.advanced_ctrl_frame)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="From (YYYY-MM-DD):").pack(side="left", padx=(4, 2))
        ttk.Entry(row2, textvariable=self.from_date_var, width=12).pack(side="left", padx=2)
        ttk.Label(row2, text="To:").pack(side="left", padx=(6, 2))
        ttk.Entry(row2, textvariable=self.to_date_var, width=12).pack(side="left", padx=2)
        ttk.Button(row2, text="📅 Filter & Select", command=self.date_range_select).pack(side="left", padx=4)
        ttk.Button(row2, text="Clear Date Filter", command=self.clear_date_filter).pack(side="left", padx=4)

        row3 = ttk.Frame(self.advanced_ctrl_frame)
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="Type Filter:").pack(side="left", padx=(4, 2))
        ttk.Combobox(
            row3,
            textvariable=self.type_filter_var,
            values=("all", "original", "reply", "retweet"),
            state="readonly",
            width=10
        ).pack(side="left", padx=2)
        ttk.Label(row3, text="Date Sort:").pack(side="left", padx=(12, 2))
        ttk.Combobox(
            row3,
            textvariable=self.date_sort_var,
            values=("newest", "oldest"),
            state="readonly",
            width=10
        ).pack(side="left", padx=2)
        ttk.Button(row3, text="Apply View", command=self.apply_simple_view).pack(side="left", padx=6)
        ttk.Button(row3, text="Reset View", command=self.reset_simple_view).pack(side="left", padx=4)

        self.canvas = tk.Canvas(
            parent,
            background=self.theme["panel_alt"],
            highlightthickness=0,
            borderwidth=0
        )
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self._scrollbar_cmd_tweets)
        self.scroll_frame = tk.Frame(self.canvas, bg=self.theme["panel_alt"])
        self.scroll_frame.bind("<Configure>", lambda e: self._on_tweets_configure(e))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Enter>", self._bind_tweet_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_tweet_mousewheel)
        self.scroll_frame.bind("<Enter>", self._bind_tweet_mousewheel)
        self.scroll_frame.bind("<Leave>", self._unbind_tweet_mousewheel)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0,5))
        scrollbar.pack(side="right", fill="y")

    def toggle_advanced_controls(self):
        if self.advanced_visible:
            self.advanced_ctrl_frame.pack_forget()
            self.advanced_btn_text.set("Advanced ▸")
            self.advanced_visible = False
            return
        self.advanced_ctrl_frame.pack(fill="x", pady=(0, 8))
        self.advanced_btn_text.set("Advanced ▾")
        self.advanced_visible = True

    def setup_delete_tab(self, parent):
        ttk.Label(parent, text="Selected tweets appear here automatically", font=("Arial", 10)).pack(pady=5)
        queue_wrap = ttk.Frame(parent)
        queue_wrap.pack(fill="both", expand=True, padx=10, pady=5)

        self.queue_canvas = tk.Canvas(
            queue_wrap,
            background=self.theme["panel_alt"],
            highlightthickness=0,
            borderwidth=0
        )
        queue_scrollbar = ttk.Scrollbar(queue_wrap, orient="vertical", command=self._scrollbar_cmd_queue)
        self.queue_frame = tk.Frame(self.queue_canvas, bg=self.theme["panel_alt"])
        self.queue_frame.bind("<Configure>", lambda e: self._on_queue_configure(e))
        self.queue_canvas.bind("<Enter>", self._bind_queue_mousewheel)
        self.queue_canvas.bind("<Leave>", self._unbind_queue_mousewheel)
        self.queue_canvas.create_window((0, 0), window=self.queue_frame, anchor="nw")
        self.queue_canvas.configure(yscrollcommand=queue_scrollbar.set)
        self.queue_canvas.pack(side="left", fill="both", expand=True)
        queue_scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=10)
        self.unqueue_btn = ttk.Button(btn_frame, text="Unqueue Selected", style="Unqueue.TButton", command=self.unqueue_selected)
        self.unqueue_btn.pack(side="left", padx=8)
        self.delete_btn = ttk.Button(
            btn_frame,
            text="DELETE ALL QUEUED NOW",
            style="DangerDelete.TButton",
            command=self.start_deletion
        )
        self.delete_btn.pack(side="left", padx=8)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(parent, textvariable=self.status_var, style="Status.TLabel").pack(pady=5)

        batch_frame = ttk.LabelFrame(parent, text="Active Batch", padding=10)
        batch_frame.pack(fill="x", padx=10, pady=(0, 8))

        self.batch_status_var = tk.StringVar(value="No active batch.")
        self.batch_queue_var = tk.StringVar(value="Queued batches: 0")
        ttk.Label(batch_frame, textvariable=self.batch_status_var).pack(anchor="w", pady=(0, 4))
        ttk.Label(batch_frame, textvariable=self.batch_queue_var, style="Muted.TLabel").pack(anchor="w")

        batch_btns = ttk.Frame(batch_frame)
        batch_btns.pack(anchor="w", pady=(8, 0))
        self.pause_resume_text = tk.StringVar(value="Pause")
        self.pause_resume_btn = ttk.Button(batch_btns, textvariable=self.pause_resume_text, command=self.toggle_pause_batch, state="disabled")
        self.pause_resume_btn.pack(side="left", padx=(0, 8))
        self.stop_batch_btn = ttk.Button(batch_btns, text="Stop", command=self.stop_active_batch, state="disabled")
        self.stop_batch_btn.pack(side="left")

    def setup_history_tab(self, parent):
        ttk.Label(parent, text="Deletion History & Running Tally", font=("Arial", 12, "bold"), style="Title.TLabel").pack(pady=8)
        self.stats_label = ttk.Label(parent, text="Total deleted: 0 | Original: 0 | Replies: 0 | Retweets: 0", font=("Arial", 10))
        self.stats_label.pack(pady=5)
        ttk.Label(parent, text="Past deletions (newest first). Trash=remove from history | Arrow=open on X | Envelope=edit & post").pack(anchor="w", padx=10)
        history_wrap = ttk.Frame(parent)
        history_wrap.pack(fill="both", expand=True, padx=10, pady=5)
        self.history_canvas = tk.Canvas(
            history_wrap,
            background=self.theme["panel_alt"],
            highlightthickness=0,
            borderwidth=0
        )
        history_scrollbar = ttk.Scrollbar(history_wrap, orient="vertical", command=self._scrollbar_cmd_history)
        self.history_frame = tk.Frame(self.history_canvas, bg=self.theme["panel_alt"])
        self.history_frame.bind("<Configure>", lambda e: self._on_history_configure(e))
        self.history_canvas.create_window((0, 0), window=self.history_frame, anchor="nw")
        self.history_canvas.configure(yscrollcommand=history_scrollbar.set)
        self.history_canvas.pack(side="left", fill="both", expand=True)
        history_scrollbar.pack(side="right", fill="y")
        self.history_canvas.bind("<Enter>", self._bind_history_mousewheel)
        self.history_canvas.bind("<Leave>", self._unbind_history_mousewheel)
        self.history_frame.bind("<Enter>", self._bind_history_mousewheel)
        self.history_frame.bind("<Leave>", self._unbind_history_mousewheel)
        self._history_display_cache = []

    def setup_compose_tab(self, parent):
        ttk.Label(parent, text="Edit & Post", font=("Arial", 12, "bold"), style="Title.TLabel").pack(pady=8)
        ttk.Label(parent, text="Compose a new tweet. Use Envelope on a history row to pre-fill from a deleted tweet.", style="Muted.TLabel").pack(anchor="w", padx=10)
        self.compose_text = tk.Text(parent, height=8, wrap="word", font=("Arial", 11))
        self._style_text_widget(self.compose_text)
        self.compose_text.pack(fill="x", padx=10, pady=5)
        self.compose_text.bind("<KeyRelease>", self._on_compose_key)
        self.compose_count_var = tk.StringVar(value="0 / 280")
        ttk.Label(parent, textvariable=self.compose_count_var, style="Muted.TLabel").pack(anchor="w", padx=10)
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Post", command=self.post_tweet).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="Clear", command=self._clear_compose).pack(side="left", padx=8)
        self.compose_status_var = tk.StringVar(value="")
        ttk.Label(parent, textvariable=self.compose_status_var, style="Status.TLabel").pack(anchor="w", padx=10, pady=5)

    def setup_ai_scrub_tab(self, parent):
        ttk.Label(parent, text="AI Scrub", font=("Arial", 14, "bold"), style="Title.TLabel").pack(pady=(20, 10))
        ttk.Label(parent, text="Send tweets to the AI in batches; get one combined search. Uses model/endpoint/token from Tab 2 (Authorization).",
                  style="Muted.TLabel", wraplength=700).pack(anchor="w", padx=30, pady=(0, 10))

        source_frame = ttk.Frame(parent)
        source_frame.pack(fill="x", padx=30, pady=5)
        self.ai_scrub_source_var = tk.StringVar(value="selected")
        ttk.Radiobutton(source_frame, text="Selected queue items", variable=self.ai_scrub_source_var, value="selected").pack(side="left", padx=(0, 20))
        ttk.Radiobutton(source_frame, text="All loaded tweets", variable=self.ai_scrub_source_var, value="all").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(source_frame, text="Reload saved cache and scrub all", variable=self.ai_scrub_source_var, value="cache").pack(side="left", padx=(0, 10))
        self.ai_scrub_warning_label = ttk.Label(source_frame, text="", style="Muted.TLabel")
        self.ai_scrub_warning_label.pack(side="left", padx=8)

        def on_source_change(*args):
            source = self.ai_scrub_source_var.get()
            if source == "selected":
                self.ai_scrub_warning_label.config(text="")
            elif source == "all":
                self.ai_scrub_warning_label.config(text="Scans all tweets currently loaded in this session.")
            else:
                self.ai_scrub_warning_label.config(text="Reloads my_tweets.json, merges with loaded tweets, then scans all in batches.")
            self._refresh_ai_scrub_coverage_preview()
        self.ai_scrub_source_var.trace_add("write", on_source_change)
        on_source_change()

        coverage_frame = ttk.LabelFrame(parent, text=" Coverage ", padding=8)
        coverage_frame.pack(fill="x", padx=30, pady=(6, 6))
        self.ai_scrub_loaded_count_var = tk.StringVar(value="Loaded in memory: 0")
        self.ai_scrub_cache_count_var = tk.StringVar(value="Saved cache rows: 0")
        self.ai_scrub_send_count_var = tk.StringVar(value="Rows being sent: 0")
        self.ai_scrub_batch_count_var = tk.StringVar(value="Estimated batches: 0")
        ttk.Label(coverage_frame, textvariable=self.ai_scrub_loaded_count_var, style="Muted.TLabel").pack(anchor="w")
        ttk.Label(coverage_frame, textvariable=self.ai_scrub_cache_count_var, style="Muted.TLabel").pack(anchor="w")
        ttk.Label(coverage_frame, textvariable=self.ai_scrub_send_count_var, style="Muted.TLabel").pack(anchor="w")
        ttk.Label(coverage_frame, textvariable=self.ai_scrub_batch_count_var, style="Muted.TLabel").pack(anchor="w")
        coverage_btns = ttk.Frame(coverage_frame)
        coverage_btns.pack(anchor="w", pady=(6, 0))
        ttk.Button(coverage_btns, text="Refresh counts", command=self._refresh_ai_scrub_coverage_preview).pack(side="left", padx=(0, 8))
        ttk.Button(coverage_btns, text="Import archive", command=self.import_archive_tweets).pack(side="left")

        ttk.Label(parent, text="What do you want to find or remove? (e.g. complaints, old jokes, politics)").pack(anchor="w", padx=30, pady=(10, 2))
        self.ai_scrub_prompt_text = tk.Text(parent, height=4, wrap="word", font=("Arial", 10))
        self._style_text_widget(self.ai_scrub_prompt_text)
        self.ai_scrub_prompt_text.pack(fill="x", padx=30, pady=5)

        btn_run_frame = ttk.Frame(parent)
        btn_run_frame.pack(fill="x", padx=30, pady=10)
        ttk.Button(btn_run_frame, text="Run AI Scrub", command=self._start_ai_scrub).pack(side="left", padx=(0, 8))
        self.ai_scrub_cancel_btn = ttk.Button(btn_run_frame, text="Cancel", command=self._cancel_ai_scrub, state="disabled")
        self.ai_scrub_cancel_btn.pack(side="left", padx=(0, 8))
        self.ai_scrub_progress_var = tk.StringVar(value="Idle.")
        ttk.Label(btn_run_frame, textvariable=self.ai_scrub_progress_var, style="Status.TLabel").pack(side="left", padx=8)

        results_frame = ttk.LabelFrame(parent, text=" Results ", padding=10)
        results_frame.pack(fill="both", expand=True, padx=30, pady=10)
        self.ai_scrub_compiled_var = tk.StringVar(value="")
        ttk.Label(results_frame, text="Compiled search:").pack(anchor="w")
        ttk.Label(results_frame, textvariable=self.ai_scrub_compiled_var, style="Muted.TLabel", wraplength=650).pack(anchor="w", pady=(0, 4))
        self.ai_scrub_result_var = tk.StringVar(value="")
        ttk.Label(results_frame, textvariable=self.ai_scrub_result_var, style="Muted.TLabel").pack(anchor="w", pady=(0, 8))
        action_frame = ttk.Frame(results_frame)
        action_frame.pack(fill="x")
        self.ai_scrub_apply_btn = ttk.Button(action_frame, text="Apply search", command=self._ai_scrub_apply_search, state="disabled")
        self.ai_scrub_apply_btn.pack(side="left", padx=(0, 8))
        self.ai_scrub_add_queue_btn = ttk.Button(action_frame, text="Add all matches to queue", command=self._ai_scrub_add_all_to_queue, state="disabled")
        self.ai_scrub_add_queue_btn.pack(side="left", padx=8)
        self.ai_scrub_last_compiled = ""
        self.ai_scrub_last_use_regex = False
        self._ai_scrub_running = False

    def _read_saved_tweets(self):
        if not os.path.exists(TWEETS_FILE):
            return []
        try:
            with open(TWEETS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _merge_tweet_sets(self, in_memory, from_cache):
        by_id = {}
        for t in from_cache + in_memory:
            tweet_id = str(t.get("id", "")).strip()
            if not tweet_id:
                continue
            existing = by_id.get(tweet_id)
            if existing is None:
                by_id[tweet_id] = dict(t)
            else:
                merged = dict(existing)
                merged.update(t)
                merged["id"] = tweet_id
                merged["selected"] = bool(existing.get("selected") or t.get("selected"))
                by_id[tweet_id] = merged
        merged = list(by_id.values())
        merged.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return merged

    def _get_ai_scrub_source_tweets(self, source, apply_merge=False):
        if source == "selected":
            return [t for t in self.tweets if t.get("selected")]
        if source == "all":
            return list(self.tweets)
        cached = self._read_saved_tweets()
        merged = self._merge_tweet_sets(list(self.tweets), cached)
        if apply_merge and merged:
            self.tweets = merged
            self.save_tweets()
            self.refresh_tweets_list()
            self.update_delete_preview()
        return merged

    def _refresh_ai_scrub_coverage_preview(self):
        if not hasattr(self, "ai_scrub_loaded_count_var"):
            return
        source = self.ai_scrub_source_var.get() if hasattr(self, "ai_scrub_source_var") else "selected"
        model = (self.ai_model_var.get() or "").strip() if hasattr(self, "ai_model_var") else ""
        model = model or (AI_MODELS[0] if AI_MODELS else "")
        loaded = len(self.tweets)
        cached = len(self._read_saved_tweets())
        source_tweets = self._get_ai_scrub_source_tweets(source, apply_merge=False)
        send_rows = len(source_tweets)
        est_batches = len(list(build_ai_batches(source_tweets, model))) if send_rows else 0
        self.ai_scrub_loaded_count_var.set(f"Loaded in memory: {loaded}")
        self.ai_scrub_cache_count_var.set(f"Saved cache rows: {cached}")
        self.ai_scrub_send_count_var.set(f"Rows being sent: {send_rows}")
        self.ai_scrub_batch_count_var.set(f"Estimated batches: {est_batches}")

    def _cancel_ai_scrub(self):
        self._ai_scrub_running = False
        self.ai_scrub_progress_var.set("Cancelling after current batch...")
        self.ai_scrub_cancel_btn.config(state="disabled")

    def _start_ai_scrub(self):
        prompt = (self.ai_scrub_prompt_text.get("1.0", tk.END) or "").strip()
        if not prompt:
            messagebox.showinfo("AI Scrub", "Enter a goal (e.g. tweets to delete: complaints, politics).")
            return
        token = (self.ai_token_var.get() or "").strip()
        if not token:
            messagebox.showerror("AI Scrub", "Set an API token in Tab 2 (Authorization) and save.")
            return
        source = self.ai_scrub_source_var.get() or "selected"
        tweets = self._get_ai_scrub_source_tweets(source, apply_merge=(source == "cache"))
        if source == "selected" and not tweets:
            messagebox.showinfo("AI Scrub", "Add tweets to the queue first (Posts & Replies), or choose an all-tweets mode.")
            return
        if not tweets:
            messagebox.showinfo("AI Scrub", "No tweets loaded. Fetch/import tweets first, then run AI Scrub.")
            return
        if source in ("all", "cache") and len(tweets) < 500:
            self.ai_scrub_progress_var.set(
                "AI Scrub scans loaded tweets. For full account history, fetch older until exhausted or import archive."
            )
        model = (self.ai_model_var.get() or "").strip() or (AI_MODELS[0] if AI_MODELS else "")
        endpoint = (self.ai_endpoint_var.get() or "").strip().rstrip("/") or AI_ENDPOINT_DEFAULT
        self._ai_scrub_running = True
        self.ai_scrub_apply_btn.config(state="disabled")
        self.ai_scrub_add_queue_btn.config(state="disabled")
        self.ai_scrub_cancel_btn.config(state="normal")
        self.ai_scrub_progress_var.set("Building batches…")
        self._refresh_ai_scrub_coverage_preview()

        def run():
            try:
                batches = list(build_ai_batches(tweets, model))
                total = len(batches)
                responses = []
                processed_rows = 0
                for i, batch in enumerate(batches):
                    if not self._ai_scrub_running:
                        break
                    msg = f"Batch {i + 1} of {total} | processed {processed_rows}/{len(tweets)} rows"
                    self.root.after(0, lambda m=msg: self.ai_scrub_progress_var.set(m))
                    batch_text = "\n---\n".join((t.get("text") or "") for t in batch)
                    user_prompt = f"Goal: {prompt}\n\nTweets in this batch:\n{batch_text}"
                    try:
                        q = self._call_ai_reviewer(endpoint, model, token, user_prompt)
                        if q:
                            responses.append(q)
                        processed_rows += len(batch)
                    except Exception as e:
                        self.root.after(0, lambda err=self._sanitize_for_display(str(e)): messagebox.showerror("AI Scrub batch error", err))
                        break
                self.root.after(0, lambda r=responses: self._on_ai_scrub_done(r))
            except Exception as e:
                self.root.after(0, lambda err=self._sanitize_for_display(str(e)): messagebox.showerror("AI Scrub", err))
                self.root.after(0, lambda: self.ai_scrub_progress_var.set("Error."))
                self.root.after(0, lambda: self.ai_scrub_apply_btn.config(state="disabled"))
                self.root.after(0, lambda: self.ai_scrub_add_queue_btn.config(state="disabled"))
                self.root.after(0, lambda: self._ai_scrub_clear_results_on_error())
            finally:
                self._ai_scrub_running = False
                self.root.after(0, lambda: self.ai_scrub_cancel_btn.config(state="disabled"))

        threading.Thread(target=run, daemon=True).start()

    def _ai_scrub_clear_results_on_error(self):
        """Clear AI Scrub result display to 0 matched when run fails before/during batches (main-thread only)."""
        self.ai_scrub_last_compiled = ""
        self.ai_scrub_compiled_var.set("(error – no query)")
        self.ai_scrub_result_var.set("Matched 0 tweet(s).")

    def _on_ai_scrub_done(self, responses):
        self.ai_scrub_progress_var.set("Compiling…")
        self.root.update_idletasks()
        use_regex = self.use_regex_var.get()
        compiled, use_regex_final = self._compile_ai_responses(responses, use_regex)
        self.ai_scrub_last_compiled = compiled or ""
        self.ai_scrub_last_use_regex = use_regex_final
        if not compiled:
            self.ai_scrub_compiled_var.set("(no query)")
            self.ai_scrub_result_var.set("Matched 0 tweet(s).")
            self.ai_scrub_progress_var.set("Done. Matched 0 tweets.")
        else:
            self.ai_scrub_compiled_var.set(compiled)
            self._apply_ai_compiled_search(compiled, use_regex_final)
            matched = len(self._get_display_tweets())
            self.ai_scrub_result_var.set(f"Matched {matched} tweet(s).")
            self.ai_scrub_progress_var.set(f"Done. Matched {matched} tweets.")
        self.ai_scrub_apply_btn.config(state="normal")
        self.ai_scrub_add_queue_btn.config(state="normal")
        self.ai_scrub_cancel_btn.config(state="disabled")

    def _ai_scrub_apply_search(self):
        if self.ai_scrub_last_compiled:
            self._apply_ai_compiled_search(self.ai_scrub_last_compiled, self.ai_scrub_last_use_regex)
            matched = len(self._get_display_tweets())
            self.ai_scrub_result_var.set(f"Matched {matched} tweet(s).")
            messagebox.showinfo("AI Scrub", f"Applied search. Showing {matched} tweet(s).")

    def _ai_scrub_add_all_to_queue(self):
        if self.ai_scrub_last_compiled:
            self._apply_ai_compiled_search(self.ai_scrub_last_compiled, self.ai_scrub_last_use_regex)
        for t in self._get_display_tweets():
            t["selected"] = True
        self.refresh_tweets_list()
        self.update_delete_preview()
        count = len(self._get_display_tweets())
        self.notebook.select(3)
        messagebox.showinfo("AI Scrub", f"Added {count} match(es) to the deletion queue.")

    # ====================== CREDENTIALS ======================
    def load_credentials(self):
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, encoding="utf-8") as f:
                    creds = json.load(f)
                for var, key in zip(
                    self.cred_vars,
                    ["consumer_key", "consumer_secret", "access_token", "access_token_secret", "bearer_token"]
                ):
                    var.set(creds.get(key, ""))
                self.ai_endpoint_var.set(creds.get("ai_endpoint", AI_ENDPOINT_DEFAULT))
                self.ai_model_var.set(creds.get("ai_model", AI_MODELS[0] if AI_MODELS else ""))
                self.ai_token_var.set(creds.get("ai_token", ""))
                self.init_client()
            except (json.JSONDecodeError, OSError, KeyError):
                pass

    def _normalize_bearer_token(self, bearer_token):
        token = (bearer_token or "").strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        return token

    def save_credentials(self):
        bearer_token = self._normalize_bearer_token(self.cred_vars[4].get())
        self.cred_vars[4].set(bearer_token)
        creds = {
            "consumer_key": self.cred_vars[0].get().strip(),
            "consumer_secret": self.cred_vars[1].get().strip(),
            "access_token": self.cred_vars[2].get().strip(),
            "access_token_secret": self.cred_vars[3].get().strip(),
            "bearer_token": bearer_token,
            "ai_endpoint": self.ai_endpoint_var.get().strip() or AI_ENDPOINT_DEFAULT,
            "ai_model": self.ai_model_var.get().strip() or (AI_MODELS[0] if AI_MODELS else ""),
            "ai_token": self.ai_token_var.get().strip(),
        }
        with open(CREDENTIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2)
        messagebox.showinfo("Saved", "Credentials saved locally.")
        self.init_client()

    def init_client(self):
        self.user_client = None
        self.bearer_client = None
        self.read_client = None
        self.client = None

        consumer_key = self.cred_vars[0].get().strip()
        consumer_secret = self.cred_vars[1].get().strip()
        access_token = self.cred_vars[2].get().strip()
        access_token_secret = self.cred_vars[3].get().strip()
        bearer_token = self._normalize_bearer_token(self.cred_vars[4].get())
        self.cred_vars[4].set(bearer_token)

        if consumer_key and consumer_secret and access_token and access_token_secret:
            try:
                self.user_client = tweepy.Client(
                    consumer_key=consumer_key,
                    consumer_secret=consumer_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret,
                    wait_on_rate_limit=True
                )
            except Exception:
                self.user_client = None

        if bearer_token:
            try:
                self.bearer_client = tweepy.Client(
                    bearer_token=bearer_token,
                    wait_on_rate_limit=True
                )
            except Exception:
                self.bearer_client = None

        # Keep legacy alias for delete path; explicitly user-auth only.
        self.client = self.user_client
        self.read_client = self.bearer_client or self.user_client

    def _auth_hint_for_status(self, status_code):
        hints = {
            400: "Bad request. Confirm no extra spaces/newlines in copied keys.",
            401: "Unauthorized. Often invalid/rotated token or wrong auth mode for this endpoint.",
            403: "Forbidden. App permissions/tier may not allow this endpoint.",
            429: "Rate limited. Try again after reset window.",
            500: "X API server error. Retry shortly."
        }
        return hints.get(status_code, "See response body snippet for X API details.")

    def _status_code_from_error(self, err):
        response = getattr(err, "response", None)
        if response is None:
            return None
        try:
            return response.status_code
        except Exception:
            return None

    def _fetch_timeline_batch(self, api_client, user_id, since_id=None, until_id=None, use_user_auth=False):
        all_new = []
        pagination_token = None
        while True:
            params = {
                "id": user_id,
                "max_results": 100,
                "pagination_token": pagination_token,
                "tweet_fields": ["created_at", "referenced_tweets", "in_reply_to_user_id", "text"],
            }
            if since_id:
                params["since_id"] = since_id
            if until_id:
                params["until_id"] = until_id
            if use_user_auth:
                params["user_auth"] = True

            response = api_client.get_users_tweets(**params)
            if not response.data:
                break
            for t in response.data:
                tweet_type = "original"
                if t.referenced_tweets:
                    for ref in t.referenced_tweets:
                        if ref.type == "retweeted":
                            tweet_type = "retweet"
                            break
                        if ref.type == "replied_to":
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

            meta = response.meta or {}
            if "next_token" not in meta:
                break
            pagination_token = meta["next_token"]
            time.sleep(1.1)
        return all_new

    def _sanitize_for_display(self, text):
        """Redact potential tokens/secrets from error text before showing to user."""
        if not text or not isinstance(text, str):
            return text
        # Redact Bearer tokens (alphanumeric + underscore, 20+ chars)
        text = re.sub(r"[Bb]earer\s+[A-Za-z0-9_-]{20,}", "Bearer [REDACTED]", text)
        # Redact long hex-like strings that might be tokens
        text = re.sub(r"\b[A-Za-z0-9_-]{40,}\b", "[REDACTED]", text)
        return text

    def _bind_tooltip(self, widget, full_text):
        """Bind hover to show full text in a tooltip. full_text can be empty to skip tooltip."""
        if not full_text:
            return
        def on_enter(ev, t=full_text):
            if self._tooltip_after_id:
                self.root.after_cancel(self._tooltip_after_id)
            self._tooltip_after_id = self.root.after(400, lambda: self._show_tooltip(widget, t))
        def on_leave(_ev):
            if self._tooltip_after_id:
                self.root.after_cancel(self._tooltip_after_id)
                self._tooltip_after_id = None
            self._hide_tooltip()
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _show_tooltip(self, widget, text):
        self._hide_tooltip()
        self._tooltip_win = tk.Toplevel(self.root)
        self._tooltip_win.wm_overrideredirect(True)
        self._tooltip_win.wm_geometry("+0+0")
        lbl = tk.Label(
            self._tooltip_win,
            text=text,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            justify="left",
            wraplength=450,
            padx=8,
            pady=6,
            relief="solid",
            borderwidth=1,
        )
        lbl.pack()
        self._tooltip_win.update_idletasks()
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 4
        self._tooltip_win.wm_geometry(f"+{x}+{y}")

    def _hide_tooltip(self):
        if self._tooltip_win:
            try:
                self._tooltip_win.destroy()
            except tk.TclError:
                pass
            self._tooltip_win = None

    def _build_error_details(self, err):
        msg = self._sanitize_for_display(str(err))
        lines = [f"Error type: {type(err).__name__}", f"Message: {msg}"]
        response = getattr(err, "response", None)
        if response is not None:
            try:
                status_code = response.status_code
                lines.append(f"HTTP status: {status_code}")
                lines.append(f"Likely cause: {self._auth_hint_for_status(status_code)}")
            except Exception:
                pass
            try:
                body = response.text.strip()
                if body:
                    snippet = self._sanitize_for_display(body[:700])
                    suffix = "..." if len(body) > 700 else ""
                    lines.append("Response body:")
                    lines.append(snippet + suffix)
            except Exception:
                pass
            try:
                headers = response.headers
                if headers:
                    remaining = headers.get("x-rate-limit-remaining")
                    reset = headers.get("x-rate-limit-reset")
                    if remaining is not None:
                        lines.append(f"Rate limit remaining: {remaining}")
                    if reset is not None:
                        lines.append(f"Rate limit reset (epoch): {reset}")
            except Exception:
                pass
        return "\n".join(lines)

    def test_auth(self):
        missing = []
        if not self.cred_vars[0].get().strip():
            missing.append("consumer key")
        if not self.cred_vars[1].get().strip():
            missing.append("consumer secret")
        if not self.cred_vars[2].get().strip():
            missing.append("access token")
        if not self.cred_vars[3].get().strip():
            missing.append("access token secret")
        if missing:
            messagebox.showerror("Missing Credentials", "Missing: " + ", ".join(missing))
            return
        if not self.user_client:
            self.init_client()
        if not self.user_client:
            messagebox.showerror("Error", "No credentials loaded")
            return
        try:
            me = self.user_client.get_me(user_fields=["username"], user_auth=True)
            username = getattr(me.data, "username", "unknown")
            user_id = getattr(me.data, "id", "unknown")
            probe = self.user_client.get_users_tweets(id=user_id, max_results=5, user_auth=True)
            fetched = len(probe.data) if probe and probe.data else 0
            messagebox.showinfo(
                "User Auth Success (RW)",
                f"OAuth user auth is working.\nUsername: @{username}\nUser ID: {user_id}\n\n"
                f"Tweet-list endpoint probe succeeded (returned {fetched} tweet(s)).\n"
                "This confirms your configured user-auth path can list your timeline."
            )
        except Exception as e:
            details = self._build_error_details(e)
            messagebox.showerror("User Auth Failed (RW)", details)

    def test_bearer_auth(self):
        bearer = self._normalize_bearer_token(self.cred_vars[4].get())
        if not bearer:
            messagebox.showerror("Missing Bearer Token", "Enter a bearer token first.")
            return
        self.cred_vars[4].set(bearer)
        try:
            self.init_client()
            if not self.bearer_client:
                raise RuntimeError("Failed to initialize bearer client. Check token format/value.")
            probe_user = self.bearer_client.get_user(username="TwitterDev", user_fields=["username"])
            username = getattr(probe_user.data, "username", "TwitterDev")
            user_id = getattr(probe_user.data, "id", "unknown")
            messagebox.showinfo(
                "Bearer Token Success (RO)",
                f"Bearer token works for read-only calls.\nProbe account: @{username}\nUser ID: {user_id}\n\n"
                "Note: Bearer auth cannot delete your tweets."
            )
        except Exception as e:
            details = self._build_error_details(e)
            messagebox.showerror("Bearer Token Failed (RO)", details)

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

    def _load_archive_payload(self, path):
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            raise ValueError("File is empty.")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # tweets.js usually starts with: window.YTD.tweets.part0 = [...]
        first_obj = content.find("{")
        first_arr = content.find("[")
        starts = [idx for idx in (first_obj, first_arr) if idx != -1]
        if not starts:
            raise ValueError("Could not find JSON object/array in archive file.")
        start = min(starts)
        trailing = content[start:].rstrip().rstrip(";").strip()
        return json.loads(trailing)

    def _parse_archive_records(self, payload):
        rows = []
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            if isinstance(payload.get("tweets"), list):
                rows = payload["tweets"]
            elif isinstance(payload.get("tweet"), dict):
                rows = [payload]
            else:
                for value in payload.values():
                    if isinstance(value, list):
                        rows = value
                        break
        if not isinstance(rows, list):
            raise ValueError("Unsupported archive structure.")
        return rows

    def _format_archive_created_at(self, raw_value):
        if not raw_value:
            return "N/A"
        text = str(raw_value).strip()
        for fmt in ("%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                dt = datetime.strptime(text, fmt)
                return dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                continue
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return "N/A"

    def _map_archive_row(self, row):
        if not isinstance(row, dict):
            return None
        tweet = row.get("tweet") if isinstance(row.get("tweet"), dict) else row
        tweet_id = str(tweet.get("id_str") or tweet.get("id") or "").strip()
        if not tweet_id:
            return None
        text = (tweet.get("full_text") or tweet.get("text") or "").strip()
        created_at = self._format_archive_created_at(tweet.get("created_at"))

        tweet_type = "original"
        lower_text = text.lower()
        if lower_text.startswith("rt @"):
            tweet_type = "retweet"
        elif tweet.get("in_reply_to_status_id") or tweet.get("in_reply_to_status_id_str") or tweet.get("in_reply_to_user_id") or tweet.get("in_reply_to_user_id_str"):
            tweet_type = "reply"

        return {
            "id": tweet_id,
            "text": text[:280],
            "created_at": created_at,
            "type": tweet_type,
            "selected": False
        }

    def import_archive_tweets(self):
        path = filedialog.askopenfilename(
            title="Import X Archive Tweets",
            filetypes=[
                ("Tweet archive files", "*.json *.js"),
                ("JSON files", "*.json"),
                ("JavaScript files", "*.js"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        try:
            payload = self._load_archive_payload(path)
            rows = self._parse_archive_records(payload)
            parsed = 0
            invalid = 0
            duplicates = 0
            added = 0
            existing_ids = {t.get("id") for t in self.tweets}
            imported = []

            for row in rows:
                mapped = self._map_archive_row(row)
                if mapped is None:
                    invalid += 1
                    continue
                parsed += 1
                if mapped["id"] in existing_ids:
                    duplicates += 1
                    continue
                imported.append(mapped)
                existing_ids.add(mapped["id"])
                added += 1

            if imported:
                self.tweets.extend(imported)
                self.tweets.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                self.save_tweets()
                self.refresh_tweets_list()
                self.update_delete_preview()
                self._refresh_ai_scrub_coverage_preview()

            messagebox.showinfo(
                "Import Complete",
                f"File: {os.path.basename(path)}\n"
                f"Parsed rows: {parsed}\n"
                f"Added: {added}\n"
                f"Skipped duplicates: {duplicates}\n"
                f"Skipped invalid: {invalid}"
            )
        except Exception as e:
            messagebox.showerror("Import Failed", f"Could not import archive file.\n\n{self._sanitize_for_display(str(e))}")

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
    def fetch_tweets(self, direction="newer"):
        if direction not in ("newer", "older"):
            direction = "newer"
        if not self.user_client and not self.bearer_client:
            self.init_client()
        if not self.user_client:
            messagebox.showerror("Error", "User auth credentials are required to resolve your account. Fill Tab 2 (Authorization) first.")
            return
        if not self.read_client:
            messagebox.showerror("Error", "Please set up credentials first (Tab 2 – Authorization).")
            return
        self.status_var.set(f"Fetching {direction} tweets...")
        self.root.update()
        try:
            user = self.user_client.get_me(user_auth=True)
            user_id = user.data.id
            tweet_ids = []
            for t in self.tweets:
                try:
                    tweet_ids.append(int(t["id"]))
                except (ValueError, KeyError, TypeError):
                    continue
            since_id = None
            until_id = None
            if tweet_ids:
                if direction == "newer":
                    since_id = str(max(tweet_ids))
                else:
                    min_id = min(tweet_ids)
                    if min_id > 0:
                        until_id = str(min_id - 1)

            primary_client = self.read_client
            primary_user_auth = primary_client is self.user_client
            all_new = []
            try:
                all_new = self._fetch_timeline_batch(
                    api_client=primary_client,
                    user_id=user_id,
                    since_id=since_id,
                    until_id=until_id,
                    use_user_auth=primary_user_auth
                )
            except Exception as primary_error:
                primary_status = self._status_code_from_error(primary_error)
                alternate_client = self.user_client if primary_client is self.bearer_client else self.bearer_client
                if primary_status == 401 and alternate_client:
                    alternate_user_auth = alternate_client is self.user_client
                    all_new = self._fetch_timeline_batch(
                        api_client=alternate_client,
                        user_id=user_id,
                        since_id=since_id,
                        until_id=until_id,
                        use_user_auth=alternate_user_auth
                    )
                    mode_name = "user auth" if alternate_user_auth else "bearer token"
                    self.status_var.set(f"{direction.title()} fetch fallback succeeded via {mode_name}.")
                else:
                    raise primary_error

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
            self._refresh_ai_scrub_coverage_preview()
            messagebox.showinfo("Done", f"Added {added} {direction} tweet(s). Total now: {len(self.tweets)}")
        except Exception as e:
            details = self._build_error_details(e)
            if self._status_code_from_error(e) == 401:
                details += (
                    "\n\nActionable checks:\n"
                    "• Re-save all keys/tokens (rotated credentials are common).\n"
                    "• Confirm app tier/permissions allow /2/users/:id/tweets.\n"
                    "• If bearer token starts with 'Bearer ', paste just the token string."
                )
            messagebox.showerror("Fetch Error", details)
        finally:
            self.status_var.set("Ready")

    # ====================== AI REVIEWER ======================
    def open_ai_reviewer(self):
        win = tk.Toplevel(self.root)
        win.title("AI Reviewer")
        win.geometry("520x280")
        win.configure(bg=self.theme["panel_bg"])
        prompt_text = tk.Text(win, height=8, wrap="word", font=("Arial", 11))
        self._style_text_widget(prompt_text)
        prompt_text.pack(fill="both", expand=True, padx=10, pady=10)
        default_prompt = "Ask the AI what you're looking for"
        prompt_text.insert("1.0", default_prompt)
        prompt_text.focus_set()

        def send():
            prompt = prompt_text.get("1.0", tk.END).strip()
            if not prompt or prompt == default_prompt:
                messagebox.showinfo("AI Reviewer", "Enter a question or description (e.g. tweets about X, replies from 2023).")
                return
            token = self.ai_token_var.get().strip()
            if not token:
                messagebox.showerror("AI Reviewer", "Set an API token in Tab 2 – Authorization (AI Reviewer section) and save.")
                return
            endpoint = (self.ai_endpoint_var.get().strip() or AI_ENDPOINT_DEFAULT).rstrip("/")
            model = self.ai_model_var.get().strip() or (AI_MODELS[0] if AI_MODELS else "")
            try:
                query = self._call_ai_reviewer(endpoint, model, token, prompt)
                if query:
                    self.search_var.set(query)
                    self.search_and_select()
                    win.destroy()
                    self.status_var.set("Filter applied from AI suggestion.")
                else:
                    messagebox.showinfo("AI Reviewer", "No search suggestion returned. Try rephrasing.")
            except Exception as e:
                messagebox.showerror("AI Reviewer", self._sanitize_for_display(str(e)))

        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Send", command=send).pack(side="left", padx=4)

    def _compile_ai_responses(self, responses, use_regex):
        """Combine batch response strings into one search query. Returns (compiled_query, use_regex)."""
        parts = [s.strip() for s in responses if (s or "").strip()]
        if not parts:
            return "", False
        if use_regex:
            combined = "|".join(parts)
            try:
                re.compile(self._normalize_for_search(combined))
                return combined, True
            except re.error:
                pass
        return ",".join(parts), False

    def _apply_ai_compiled_search(self, compiled_query, use_regex):
        """Set search filter to compiled query and refresh list/queue."""
        self.search_filter_query = compiled_query or ""
        self.search_filter_regex = use_regex
        self.search_var.set(compiled_query)
        self.use_regex_var.set(use_regex)
        self.refresh_tweets_list()
        self.update_delete_preview()

    def _call_ai_reviewer(self, endpoint, model, token, user_prompt):
        """Call OpenAI-compatible chat API. Returns suggested search string. Never logs token."""
        base = (endpoint or "").strip().rstrip("/")
        url = f"{base}/chat/completions"
        payload = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "You help filter a list of tweets. Reply with ONLY a short search query or regex (one line) that would find the tweets the user wants. No explanation, no quotes, just the search string."},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 200,
        }).encode("utf-8")
        _ai_logger.info("AI request | endpoint=%s | model=%s | prompt_len=%d", endpoint, model, len(user_prompt))
        _ai_logger.debug("AI request prompt (truncated): %s", (user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt))
        req = Request(url, data=payload, method="POST", headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer " + token,
            "User-Agent": AI_REQUEST_USER_AGENT,
        })
        try:
            with urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)
            _ai_logger.info("AI response OK | model=%s | response_len=%d", model, len(raw))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:500]
            _ai_logger.warning("AI HTTP error | status=%s | endpoint=%s | model=%s | body=%s", e.code, endpoint, model, self._sanitize_for_display(body)[:300])
            raise RuntimeError(f"AI API error {e.code}: {self._sanitize_for_display(body)}")
        except urllib.error.URLError as e:
            _ai_logger.warning("AI request failed | endpoint=%s | reason=%s", endpoint, self._sanitize_for_display(str(e.reason)))
            raise RuntimeError(f"AI API request failed: {self._sanitize_for_display(str(e.reason))}")
        choice = (data.get("choices") or [None])[0]
        if not choice:
            _ai_logger.debug("AI response had no choices")
            return None
        content = (choice.get("message") or {}).get("content")
        if not content:
            _ai_logger.debug("AI response choice had no content")
            return None
        result = content.strip().split("\n")[0].strip()
        _ai_logger.debug("AI suggested query: %s", (result[:150] + "..." if len(result) > 150 else result))
        return result

    # ====================== SEARCH (Regex supported) ======================
    def search_and_select(self):
        query = self.search_var.get().strip()
        if not query:
            self.search_filter_query = ""
            self.search_filter_regex = False
            self.refresh_tweets_list()
            self.update_delete_preview()
            messagebox.showinfo("Search Cleared", "Showing all tweets again.")
            return
        if self.use_regex_var.get():
            try:
                re.compile(self._normalize_for_search(query))
            except re.error:
                messagebox.showerror("Regex Error", "Invalid regex pattern. Fix it before filtering.")
                return
            self.search_filter_regex = True
        else:
            self.search_filter_regex = False
        self.search_filter_query = query
        count = 0
        for tweet in self.tweets:
            text = tweet.get("text") or ""
            normalized_text = self._normalize_for_search(text)
            if self.search_filter_regex:
                normalized_query = self._normalize_for_search(query)
                if re.search(normalized_query, normalized_text, re.IGNORECASE):
                    count += 1
            else:
                keywords = [self._normalize_for_search(w.strip()) for w in query.split(",") if w.strip()]
                if any(kw in normalized_text for kw in keywords):
                    count += 1
        self.refresh_tweets_list()
        self.update_delete_preview()
        messagebox.showinfo("Filter Applied", f"Showing {count} matching tweet(s). No queue selections were changed.")

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

    def apply_simple_view(self):
        self.refresh_tweets_list()
        self.update_delete_preview()

    def reset_simple_view(self):
        self.type_filter_var.set("all")
        self.date_sort_var.set("newest")
        self.refresh_tweets_list()
        self.update_delete_preview()

    # ====================== LIST DISPLAY ======================
    def _bind_tweet_mousewheel(self, _event=None):
        if self._tweet_wheel_bound:
            return
        self.canvas.bind_all("<MouseWheel>", self._on_tweet_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_tweet_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_tweet_mousewheel)
        self._tweet_wheel_bound = True

    def _unbind_tweet_mousewheel(self, _event=None):
        if not self._tweet_wheel_bound:
            return
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")
        self._tweet_wheel_bound = False

    def _on_tweet_mousewheel(self, event):
        if getattr(event, "num", None) == 4:
            self.canvas.yview_scroll(-1, "units")
            return
        if getattr(event, "num", None) == 5:
            self.canvas.yview_scroll(1, "units")
            return

        delta = getattr(event, "delta", 0)
        if delta == 0:
            return
        if platform.system() == "Darwin":
            step = -1 if delta > 0 else 1
        else:
            step = int(-delta / 120)
            if step == 0:
                step = -1 if delta > 0 else 1
        self.canvas.yview_scroll(step, "units")
        self.root.after(50, self._maybe_load_more_tweets)

    def _scrollbar_cmd_tweets(self, *args):
        self.canvas.yview(*args)
        self.root.after(50, self._maybe_load_more_tweets)

    def _on_tweets_configure(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _maybe_load_more_tweets(self):
        try:
            top, bottom = self.canvas.yview()
            if bottom >= 0.92 and self._tweets_rendered_count < len(self._display_tweets_cache):
                self._append_tweets_chunk()
        except Exception:
            pass

    def _create_tweet_row(self, parent_frame, tweet, colors):
        var = tk.BooleanVar(value=tweet.get("selected", False))
        self.check_vars[tweet["id"]] = var
        row = tk.Frame(parent_frame, bg=colors.get(tweet["type"], self.theme["panel_alt"]))
        row.pack(fill="x", padx=5, pady=2)
        row.bind("<Enter>", self._bind_tweet_mousewheel)
        row_bg = colors.get(tweet["type"], self.theme["panel_alt"])
        chk = tk.Checkbutton(
            row,
            variable=var,
            bg=row_bg,
            fg=self.theme["text"],
            activebackground=row_bg,
            activeforeground=self.theme["text"],
            selectcolor=row_bg,
            highlightthickness=0,
            command=lambda t=tweet, v=var: self.on_check_toggle(t, v)
        )
        chk.pack(side="left", padx=5)
        chk.bind("<Enter>", self._bind_tweet_mousewheel)
        text = tweet.get("text") or ""
        txt = f"{tweet['created_at']} | {tweet['type'].upper():7} | {text[:110]}{'...' if len(text) > 110 else ''}"
        tweet_label = tk.Label(
            row,
            text=txt,
            anchor="w",
            bg=row_bg,
            fg=self.theme["text"],
            justify="left",
            wraplength=850
        )
        tweet_label.pack(side="left", fill="x", padx=5)
        tweet_label.bind("<Enter>", self._bind_tweet_mousewheel)
        self._bind_tooltip(tweet_label, text)
        return row

    def _append_tweets_chunk(self):
        colors = {
            "original": self.theme["tweet_original_bg"],
            "reply": self.theme["tweet_reply_bg"],
            "retweet": self.theme["tweet_retweet_bg"]
        }
        start = self._tweets_rendered_count
        end = min(start + CHUNK_SIZE, len(self._display_tweets_cache))
        for tweet in self._display_tweets_cache[start:end]:
            self._create_tweet_row(self.scroll_frame, tweet, colors)
        self._tweets_rendered_count = end
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _get_display_tweets(self):
        display_tweets = list(self.tweets)
        search_query = (self.search_filter_query or "").strip()
        if search_query:
            if self.search_filter_regex:
                normalized_query = self._normalize_for_search(search_query)
                display_tweets = [
                    t for t in display_tweets
                    if re.search(normalized_query, self._normalize_for_search(t.get("text") or ""), re.IGNORECASE)
                ]
            else:
                keywords = [self._normalize_for_search(w.strip()) for w in search_query.split(",") if w.strip()]
                if keywords:
                    display_tweets = [
                        t for t in display_tweets
                        if any(kw in self._normalize_for_search(t.get("text") or "") for kw in keywords)
                    ]
        selected_type = (self.type_filter_var.get() or "all").strip().lower()
        if selected_type != "all":
            display_tweets = [t for t in display_tweets if (t.get("type") or "").lower() == selected_type]
        reverse = (self.date_sort_var.get() or "newest").lower() != "oldest"
        display_tweets.sort(key=lambda x: x.get("created_at", ""), reverse=reverse)
        return display_tweets

    def _normalize_for_search(self, text):
        normalized = unicodedata.normalize("NFKD", text or "")
        without_marks = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return without_marks.casefold()

    def refresh_tweets_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()
        self._display_tweets_cache = self._get_display_tweets()
        self._tweets_rendered_count = 0
        colors = {
            "original": self.theme["tweet_original_bg"],
            "reply": self.theme["tweet_reply_bg"],
            "retweet": self.theme["tweet_retweet_bg"]
        }
        for tweet in self._display_tweets_cache[:CHUNK_SIZE]:
            self._create_tweet_row(self.scroll_frame, tweet, colors)
        self._tweets_rendered_count = min(CHUNK_SIZE, len(self._display_tweets_cache))
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _bind_queue_mousewheel(self, _event=None):
        if self._queue_wheel_bound:
            return
        self.root.bind_all("<MouseWheel>", self._on_queue_mousewheel)
        self.root.bind_all("<Button-4>", self._on_queue_mousewheel)
        self.root.bind_all("<Button-5>", self._on_queue_mousewheel)
        self._queue_wheel_bound = True

    def _unbind_queue_mousewheel(self, _event=None):
        if not self._queue_wheel_bound:
            return
        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")
        self._queue_wheel_bound = False

    def _bind_history_mousewheel(self, _event=None):
        if self._history_wheel_bound:
            return
        self.root.bind_all("<MouseWheel>", self._on_history_mousewheel)
        self.root.bind_all("<Button-4>", self._on_history_mousewheel)
        self.root.bind_all("<Button-5>", self._on_history_mousewheel)
        self._history_wheel_bound = True

    def _unbind_history_mousewheel(self, _event=None):
        if not self._history_wheel_bound:
            return
        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")
        self._history_wheel_bound = False

    def _on_history_mousewheel(self, event):
        try:
            if getattr(event, "num", None) == 4:
                self.history_canvas.yview_scroll(-1, "units")
                return
            if getattr(event, "num", None) == 5:
                self.history_canvas.yview_scroll(1, "units")
                return
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return
            if platform.system() == "Darwin":
                step = -1 if delta > 0 else 1
            else:
                step = int(-delta / 120)
                if step == 0:
                    step = -1 if delta > 0 else 1
            self.history_canvas.yview_scroll(step, "units")
        except Exception:
            pass
        self.root.after(50, self._maybe_load_more_history)

    def _on_queue_mousewheel(self, event):
        try:
            if getattr(event, "num", None) == 4:
                self.queue_canvas.yview_scroll(-1, "units")
                return
            if getattr(event, "num", None) == 5:
                self.queue_canvas.yview_scroll(1, "units")
                return
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return
            if platform.system() == "Darwin":
                step = -1 if delta > 0 else 1
            else:
                step = int(-delta / 120)
                if step == 0:
                    step = -1 if delta > 0 else 1
            self.queue_canvas.yview_scroll(step, "units")
        except Exception:
            pass
        self.root.after(50, self._maybe_load_more_queue)

    def _scrollbar_cmd_queue(self, *args):
        self.queue_canvas.yview(*args)
        self.root.after(50, self._maybe_load_more_queue)

    def _on_queue_configure(self, e):
        self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all"))

    def _maybe_load_more_queue(self):
        try:
            top, bottom = self.queue_canvas.yview()
            if bottom >= 0.92 and self._queue_rendered_count < len(self._queue_display_cache):
                self._append_queue_chunk()
        except Exception:
            pass

    def _create_queue_row(self, parent_frame, t, var):
        row = tk.Frame(parent_frame, bg=self.theme["panel_alt"])
        row.pack(fill="x", padx=4, pady=2)
        row.bind("<Enter>", self._bind_queue_mousewheel)
        tk.Checkbutton(
            row,
            variable=var,
            bg=self.theme["panel_alt"],
            fg=self.theme["text"],
            activebackground=self.theme["panel_alt"],
            activeforeground=self.theme["text"],
            selectcolor=self.theme["panel_alt"],
            highlightthickness=0
        ).pack(side="left", padx=4)
        full_text = t.get("text") or ""
        txt = f"{t['created_at']} | {t.get('type', 'unknown')} | {full_text[:85]}{'...' if len(full_text) > 85 else ''}"
        lbl = tk.Label(row, text=txt, bg=self.theme["panel_alt"], fg=self.theme["text"],
                       justify="left", anchor="w", wraplength=900)
        lbl.pack(side="left", fill="x", expand=True, padx=4)
        lbl.bind("<Enter>", self._bind_queue_mousewheel)
        self._bind_tooltip(lbl, full_text)

    def _append_queue_chunk(self):
        start = self._queue_rendered_count
        end = min(start + CHUNK_SIZE, len(self._queue_display_cache))
        for t, var in self._queue_display_cache[start:end]:
            self._create_queue_row(self.queue_frame, t, var)
        self._queue_rendered_count = end
        self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all"))

    def on_check_toggle(self, tweet, var):
        tweet["selected"] = var.get()
        self.update_delete_preview()

    def select_all(self):
        for t in self._get_display_tweets():
            t["selected"] = True
        self.refresh_tweets_list()
        self.update_delete_preview()

    def deselect_all(self):
        for t in self._get_display_tweets():
            t["selected"] = False
        self.refresh_tweets_list()
        self.update_delete_preview()

    def update_delete_preview(self):
        selected = [t for t in self.tweets if t["selected"]]
        selected_ids = {t["id"] for t in selected}
        for tweet_id in list(self.queue_vars.keys()):
            if tweet_id not in selected_ids:
                del self.queue_vars[tweet_id]

        for t in selected:
            if t["id"] not in self.queue_vars:
                self.queue_vars[t["id"]] = tk.BooleanVar(value=True)

        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        if not selected:
            tk.Label(
                self.queue_frame,
                text="No tweets selected yet.",
                bg=self.theme["panel_alt"],
                fg=self.theme["muted_text"],
                anchor="w"
            ).pack(fill="x", padx=6, pady=6)
            return

        selected.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        self._queue_display_cache = [(t, self.queue_vars[t["id"]]) for t in selected]
        self._queue_rendered_count = 0
        for t, var in self._queue_display_cache[:CHUNK_SIZE]:
            self._create_queue_row(self.queue_frame, t, var)
        self._queue_rendered_count = min(CHUNK_SIZE, len(self._queue_display_cache))
        self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all"))

    def unqueue_selected(self):
        removed = 0
        for tweet in self.tweets:
            if not tweet.get("selected"):
                continue
            queue_var = self.queue_vars.get(tweet["id"])
            if queue_var is not None and queue_var.get():
                tweet["selected"] = False
                removed += 1
        self.refresh_tweets_list()
        self.update_delete_preview()
        if removed:
            messagebox.showinfo("Unqueued", f"Removed {removed} tweet(s) from queue.")
        else:
            messagebox.showinfo("Unqueued", "No checked queue items to remove.")

    # ====================== DELETION ======================
    def _collect_checked_queue_items(self):
        selected = []
        for tweet in self.tweets:
            if not tweet.get("selected"):
                continue
            queue_var = self.queue_vars.get(tweet["id"])
            if queue_var is not None and queue_var.get():
                selected.append(tweet)
        return selected

    def _clear_staging_selection(self, tweets_to_clear):
        clear_ids = {t["id"] for t in tweets_to_clear}
        for tweet in self.tweets:
            if tweet["id"] in clear_ids:
                tweet["selected"] = False
        for tweet_id in clear_ids:
            self.queue_vars.pop(tweet_id, None)

    def _set_active_batch_controls(self, enabled):
        pause_state = "normal" if enabled else "disabled"
        stop_state = "normal" if enabled else "disabled"
        self.pause_resume_btn.config(state=pause_state)
        self.stop_batch_btn.config(state=stop_state)
        if not enabled:
            self.pause_resume_text.set("Pause")

    def _refresh_batch_panel(self):
        if self.active_batch is None:
            self.batch_status_var.set("No active batch.")
            self._set_active_batch_controls(False)
        else:
            deleted = self.active_batch["deleted"]
            failed = self.active_batch["failed"]
            total = self.active_batch["total"]
            status = self.active_batch["status"]
            self.batch_status_var.set(
                f"Batch #{self.active_batch['id']} | {status.upper()} | "
                f"Deleted {deleted} | Failed {failed} | Remaining {max(total - deleted - failed, 0)}"
            )
            self._set_active_batch_controls(status in {"running", "paused", "stopping"})
            self.pause_resume_text.set("Resume" if status == "paused" else "Pause")
        self.batch_queue_var.set(f"Queued batches: {len(self.pending_batches)}")

    def _build_batch(self, selected_items):
        self.batch_counter += 1
        snapshot = [{**tweet} for tweet in selected_items]
        return {
            "id": self.batch_counter,
            "items": snapshot,
            "total": len(snapshot),
            "deleted": 0,
            "failed": 0,
            "status": "queued",
            "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _start_batch_worker(self, batch):
        batch["status"] = "running"
        self.active_batch = batch
        self.batch_pause_event.set()
        self.batch_stop_requested = False
        self._refresh_batch_panel()
        self.status_var.set(f"Running batch #{batch['id']}...")
        threading.Thread(target=self.delete_thread, args=(batch,), daemon=True).start()

    def _start_next_pending_batch(self):
        if self.active_batch is not None or not self.pending_batches:
            self._refresh_batch_panel()
            return
        next_batch = self.pending_batches.pop(0)
        self._start_batch_worker(next_batch)

    def toggle_pause_batch(self):
        if self.active_batch is None:
            return
        if self.active_batch["status"] == "running":
            self.active_batch["status"] = "paused"
            self.batch_pause_event.clear()
        elif self.active_batch["status"] == "paused":
            self.active_batch["status"] = "running"
            self.batch_pause_event.set()
        self._refresh_batch_panel()

    def stop_active_batch(self):
        if self.active_batch is None:
            return
        self.batch_stop_requested = True
        self.batch_pause_event.set()
        self.active_batch["status"] = "stopping"
        self._refresh_batch_panel()
        self.status_var.set(f"Stopping batch #{self.active_batch['id']}...")

    def start_deletion(self):
        selected = self._collect_checked_queue_items()
        if not selected:
            messagebox.showwarning("Nothing queued", "Check at least one queued item in Tab 3.")
            return
        if not messagebox.askyesno(
            "Final Confirmation",
            f"PERMANENTLY delete {len(selected)} queued tweet(s)?\n\nThis cannot be undone."
        ):
            return
        batch = self._build_batch(selected)
        self._clear_staging_selection(selected)
        self.refresh_tweets_list()
        self.update_delete_preview()
        if self.active_batch is None:
            self._start_batch_worker(batch)
            return
        self.pending_batches.append(batch)
        self._refresh_batch_panel()
        self.status_var.set(
            f"Queued batch #{batch['id']} ({batch['total']} item(s)). "
            f"Active batch #{self.active_batch['id']} continues."
        )

    def _apply_single_deletion(self, tweet_id, history_entry):
        """Run on main thread: update tweets and history lists."""
        self.tweets = [t for t in self.tweets if t["id"] != tweet_id]
        self.deleted_history.insert(0, history_entry)
        self.save_tweets()
        self.save_history()
        self.refresh_tweets_list()
        self.update_delete_preview()
        self.refresh_history_tab()

    def delete_thread(self, batch):
        try:
            if not self.user_client:
                raise RuntimeError("User auth client is not initialized. Re-test user auth in Tab 2 (Authorization).")
            for i, tweet in enumerate(batch["items"]):
                while not self.batch_pause_event.is_set():
                    if self.batch_stop_requested:
                        break
                    time.sleep(0.2)
                if self.batch_stop_requested:
                    break
                try:
                    self.user_client.delete_tweet(tweet["id"], user_auth=True)
                    batch["deleted"] += 1
                    now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    hist_entry = {**tweet, "deleted_at": now}
                    self.root.after(0, lambda tid=tweet["id"], he=hist_entry: self._apply_single_deletion(tid, he))
                    self.root.after(
                        0,
                        lambda b=batch: self.status_var.set(
                            f"Batch #{b['id']} progress: {b['deleted']} deleted, {b['failed']} failed, "
                            f"{max(b['total'] - b['deleted'] - b['failed'], 0)} remaining"
                        )
                    )
                    self.root.after(0, self._refresh_batch_panel)
                    if (i + 1) % 50 == 0:
                        self.root.after(0, lambda: messagebox.showinfo("Rate Limit", "Waiting 15 minutes for API..."))
                        time.sleep(901)
                    time.sleep(0.6)
                except tweepy.TooManyRequests:
                    if self.batch_stop_requested:
                        break
                    self.root.after(0, lambda: messagebox.showinfo("Rate Limit", "Waiting 15 minutes..."))
                    time.sleep(901)
                except Exception as e:
                    batch["failed"] += 1
                    self.root.after(0, lambda err=self._sanitize_for_display(str(e)): self.status_var.set(f"Batch #{batch['id']} error: {err}"))
                    self.root.after(0, self._refresh_batch_panel)
                    time.sleep(2)
            self.root.after(0, lambda b=batch: self._finish_deletion_batch(b))
        except Exception as e:
            err_msg = self._sanitize_for_display(str(e))
            self.root.after(0, lambda msg=err_msg: messagebox.showerror("Error", msg))
            self.root.after(0, lambda b=batch: self._finish_deletion_batch(b))

    def _finish_deletion_batch(self, batch):
        stopped = self.batch_stop_requested
        if stopped:
            batch["status"] = "stopped"
            messagebox.showinfo(
                "Batch Stopped",
                f"Batch #{batch['id']} stopped.\nDeleted: {batch['deleted']}\nFailed: {batch['failed']}"
            )
        else:
            batch["status"] = "finished"
            messagebox.showinfo(
                "Batch Finished",
                f"Batch #{batch['id']} finished.\nDeleted: {batch['deleted']}\nFailed: {batch['failed']}"
            )
        self.active_batch = None
        self.batch_stop_requested = False
        self.batch_pause_event.set()
        self.status_var.set("Ready")
        self._refresh_batch_panel()
        self._start_next_pending_batch()

    # ====================== HISTORY ======================
    def _scrollbar_cmd_history(self, *args):
        self.history_canvas.yview(*args)
        self.root.after(50, self._maybe_load_more_history)

    def _on_history_configure(self, e):
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def _maybe_load_more_history(self):
        try:
            top, bottom = self.history_canvas.yview()
            if bottom >= 0.92 and self._history_rendered_count < len(self._history_display_cache):
                self._append_history_chunk()
        except Exception:
            pass

    def _create_history_row(self, parent_frame, h):
        row = tk.Frame(parent_frame, bg=self.theme["panel_alt"])
        row.pack(fill="x", padx=4, pady=2)
        row.bind("<Enter>", self._bind_history_mousewheel)
        ttk.Button(row, text="🗑", width=3, command=lambda h=h: self.remove_from_history(h)).pack(side="left", padx=2)
        ttk.Button(row, text="➡", width=3, command=lambda h=h: self.open_intent_tweet(h)).pack(side="left", padx=2)
        ttk.Button(row, text="✉", width=3, command=lambda h=h: self.send_history_to_compose(h)).pack(side="left", padx=2)
        full_text = h.get("text") or ""
        txt = f"{h['deleted_at']} | {h['created_at']} | {h.get('type', 'unknown').upper()} | {full_text[:85]}{'...' if len(full_text) > 85 else ''}"
        lbl = tk.Label(row, text=txt, bg=self.theme["panel_alt"], fg=self.theme["text"],
                       justify="left", anchor="w", wraplength=900)
        lbl.pack(side="left", fill="x", expand=True, padx=4)
        lbl.bind("<Enter>", self._bind_history_mousewheel)
        self._bind_tooltip(lbl, full_text)

    def _append_history_chunk(self):
        start = self._history_rendered_count
        end = min(start + CHUNK_SIZE, len(self._history_display_cache))
        for h in self._history_display_cache[start:end]:
            self._create_history_row(self.history_frame, h)
        self._history_rendered_count = end
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def remove_from_history(self, entry):
        self.deleted_history = [h for h in self.deleted_history if h != entry]
        self.save_history()
        self.refresh_history_tab()

    def open_intent_tweet(self, entry):
        text = (entry.get("text") or "")[:280]
        url = "https://twitter.com/intent/tweet?text=" + quote(text)
        webbrowser.open(url)

    def send_history_to_compose(self, entry):
        self.compose_text.delete("1.0", tk.END)
        self.compose_text.insert("1.0", (entry.get("text") or "")[:280])
        self._on_compose_key(None)
        self.notebook.select(5)

    def refresh_history_tab(self):
        total = len(self.deleted_history)
        by_type = {"original": 0, "reply": 0, "retweet": 0}
        for h in self.deleted_history:
            by_type[h.get("type", "original")] += 1
        self.stats_label.config(text=f"Total deleted: {total} | Original: {by_type['original']} | Replies: {by_type['reply']} | Retweets: {by_type['retweet']}")
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        if not self.deleted_history:
            tk.Label(self.history_frame, text="No deletions yet.", bg=self.theme["panel_alt"],
                     fg=self.theme["muted_text"], anchor="w").pack(fill="x", padx=6, pady=6)
            return
        self._history_display_cache = list(self.deleted_history)
        self._history_rendered_count = 0
        for h in self._history_display_cache[:CHUNK_SIZE]:
            self._create_history_row(self.history_frame, h)
        self._history_rendered_count = min(CHUNK_SIZE, len(self._history_display_cache))
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    # ====================== COMPOSE ======================
    def _on_compose_key(self, _event):
        text = self.compose_text.get("1.0", tk.END)
        n = len(text.rstrip("\n"))
        self.compose_count_var.set(f"{n} / 280")

    def _clear_compose(self):
        self.compose_text.delete("1.0", tk.END)
        self._on_compose_key(None)
        self.compose_status_var.set("")

    def post_tweet(self):
        body = self.compose_text.get("1.0", tk.END).strip()
        if not body:
            self.compose_status_var.set("Enter some text first.")
            return
        if len(body) > 280:
            self.compose_status_var.set("Text too long. Max 280 characters.")
            return
        if not self.user_client:
            self.init_client()
        if not self.user_client:
            self.compose_status_var.set("Set up credentials in Tab 2 (Authorization) first.")
            return
        try:
            self.user_client.create_tweet(text=body, user_auth=True)
            self.compose_text.delete("1.0", tk.END)
            self._on_compose_key(None)
            self.compose_status_var.set("Posted successfully.")
        except Exception as e:
            details = self._build_error_details(e)
            self.compose_status_var.set("Post failed: " + self._sanitize_for_display(str(e))[:80])
            messagebox.showerror("Post Failed", details)

if __name__ == "__main__":
    print("Starting PleaseDaddyElonNotTheBelt.py")
    print("Dependency check passed.")
    XBulkDeleter()