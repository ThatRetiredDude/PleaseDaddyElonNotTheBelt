#!/usr/bin/env python3
"""Entry point: dependency check, then launch the app (see the `pde` package)."""

from __future__ import annotations

from pde import deps

deps.check_dependencies()
from pde import app  # import after check (tweepy, matplotlib, tk, …)

if __name__ == "__main__":
    print("Starting PleaseDaddyElonNotTheBelt")
    print("Dependency check passed.")
    app.main()
