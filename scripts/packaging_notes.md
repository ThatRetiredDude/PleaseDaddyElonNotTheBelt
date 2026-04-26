# Optional: bundling the app (PyInstaller, etc.)

Building a double-clickable binary is **not** required to run the project (use `python PleaseDaddyElonNotTheBelt.py` or [run.sh](../run.sh) with a venv).

If you use [PyInstaller](https://pyinstaller.org/):

- You need a spec that includes **tkinter** and **matplotlib** data files; paths differ on Windows, macOS, and Linux.
- A typical starting point: `pyinstaller --onefile --windowed --name XBulkDeleter PleaseDaddyElonNotTheBelt.py` may still miss hidden imports; add `--hidden-import` for `PIL`, `matplotlib.backends.backend_tkagg`, etc. as errors appear.
- Test the built app on the **same OS** you target; do not expect one binary to work everywhere.

For distribution, many teams ship a small shell/batch script that creates a venv and runs the script instead of a frozen binary.
