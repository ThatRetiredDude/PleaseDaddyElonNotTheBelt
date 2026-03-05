#!/bin/bash
# Run PleaseDaddyElonNotTheBelt with the project's virtual environment
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  echo "No .venv found. Create it with:"
  echo "  /opt/homebrew/opt/python@3.12/bin/python3.12 -m venv .venv"
  echo "  .venv/bin/pip install tweepy"
  exit 1
fi
exec .venv/bin/python PleaseDaddyElonNotTheBelt.py
