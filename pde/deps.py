"""Import-time dependency check (before tweepy / matplotlib)."""

import platform
import sys
import tkinter as tk
from tkinter import messagebox


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


def check_dependencies() -> None:
    missing = []
    try:
        import tweepy  # noqa: F401
    except ImportError:
        missing.append("tweepy")
    try:
        import tkinter  # noqa: F401
    except ImportError:
        missing.append("tkinter")
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        missing.append("matplotlib")

    if not missing:
        return

    os_name = platform.system()
    os_release = platform.release()
    python_ver = sys.version.split()[0]

    instr = "First-time setup — missing dependencies detected\n\n"
    instr += f"OS:      {os_name} {os_release}\n"
    instr += f"Python:  {python_ver}\n\n"
    instr += "Missing packages:\n • " + "\n • ".join(missing) + "\n\n"

    if os_name == "Windows":
        instr += "Run in Command Prompt or PowerShell:\n"
        instr += f"pip install {' '.join(missing)}\n\n"
        instr += "If pip is not found try:\npy -m pip install " + " ".join(missing) + "\n"
    elif os_name == "Darwin":
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
