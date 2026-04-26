"""
Integration smoke test: construct the main window without a visible display loop.

CI uses Xvfb (see .github/workflows/ci.yml) so `tk` has a $DISPLAY.
"""

import gc

from pde.app import XBulkDeleter


def test_xbulkdeleter_instantiate_headless_no_block():
    app = XBulkDeleter(run_event_loop=False, headless=True)
    try:
        assert "Bulk Deleter" in (app.root.title() or "")
        app.root.update_idletasks()
    finally:
        app.root.destroy()
        app.root = None
        gc.collect()


def test_credential_map_missing_file_returns_empty():
    from pde import secure_creds

    a, b = secure_creds.load_credential_map("/nonexistent/please_daddy/please_daddy_please.json")
    assert a is None and b is None
