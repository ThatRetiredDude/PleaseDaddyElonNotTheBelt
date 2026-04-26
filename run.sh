#!/usr/bin/env bash
# Run PleaseDaddyElonNotTheBelt with the repo's virtual environment
set -e
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  echo "No .venv in this directory. Create it and install dependencies, for example:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements.txt"
  exit 1
fi

if ! .venv/bin/pip show tweepy >/dev/null 2>&1; then
  echo "Installing requirements into .venv …"
  .venv/bin/pip install -r requirements.txt
fi

exec .venv/bin/python PleaseDaddyElonNotTheBelt.py
