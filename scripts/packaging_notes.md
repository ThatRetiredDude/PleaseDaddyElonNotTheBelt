# Optional: bundling the app (PyInstaller, etc.)

Building a double-clickable binary is **not** required to run the project (use `python PleaseDaddyElonNotTheBelt.py` or [run.sh](../run.sh) with a venv).

If you use [PyInstaller](https://pyinstaller.org/):

- You need a spec that includes **tkinter** and **matplotlib** data files; paths differ on Windows, macOS, and Linux.
- A typical starting point: `pyinstaller --onefile --windowed --name XBulkDeleter PleaseDaddyElonNotTheBelt.py` may still miss hidden imports. Add at least: `--hidden-import` `pde.app`, `pde.paths`, `pde.constants`, `pde.deps`, `pde.ai_batching`, `pde.secure_creds`, `keyring.backends`, `keyring`, `matplotlib.backends.backend_tkagg`, and any others PyInstaller reports.
- The app loads [xeraser_analytics.py](../xeraser_analytics.py) from the repo root; keep it next to the built binary or add a `datas=` entry in a `.spec` file.
- Test the built app on the **same OS** you target; do not expect one binary to work everywhere.

For distribution, many teams ship a small shell/batch script that creates a venv and runs the script instead of a frozen binary.
