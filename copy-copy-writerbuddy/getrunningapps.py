#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

VENV_DIR = ".venv"
PYTHON = sys.executable


def run(cmd, check=True):
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def in_venv():
    # Correct & reliable on Raspberry Pi OS / Debian
    return sys.prefix != sys.base_prefix


def ensure_wmctrl():
    if shutil.which("wmctrl"):
        return

    print("[INFO] Installing wmctrl (requires sudo)...")
    subprocess.run(["sudo", "apt", "update"], check=True)
    subprocess.run(["sudo", "apt", "install", "-y", "wmctrl"], check=True)


def ensure_venv():
    if os.path.isdir(VENV_DIR):
        return

    print("[INFO] Creating virtual environment...")
    subprocess.run([PYTHON, "-m", "venv", VENV_DIR], check=True)


def relaunch_in_venv():
    if in_venv():
        return

    venv_python = os.path.join(VENV_DIR, "bin", "python")
    print("[INFO] Relaunching inside virtual environment...")
    os.execv(venv_python, [venv_python] + sys.argv)


def get_gui_apps():
    """
    Uses wmctrl -lx to list GUI windows (X11 / PIXEL)
    """
    result = run(["wmctrl", "-lx"])
    apps = set()

    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3:
            wm_class = parts[2]
            apps.add(wm_class.split(".")[-1])

    return sorted(apps)


def main():
    ensure_venv()
    relaunch_in_venv()

    ensure_wmctrl()

    print("\n[RUNNING GUI APPLICATIONS]\n")
    apps = get_gui_apps()

    if not apps:
        print("No GUI applications detected.")
    else:
        for app in apps:
            print(f"- {app}")


if __name__ == "__main__":
    main()
