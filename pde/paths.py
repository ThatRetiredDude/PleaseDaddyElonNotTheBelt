"""Paths relative to the repository root (sibling to this package)."""

import os

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
# Repo root: pde/ -> parent
REPO_ROOT = os.path.normpath(os.path.join(_PACKAGE_DIR, os.pardir))

CREDENTIALS_FILE = os.path.join(REPO_ROOT, "x_credentials.json")
TWEETS_FILE = os.path.join(REPO_ROOT, "my_tweets.json")
HISTORY_FILE = os.path.join(REPO_ROOT, "deleted_history.json")
TOS_LAST_RUN_FILE = os.path.join(REPO_ROOT, "tos_last_run.json")
