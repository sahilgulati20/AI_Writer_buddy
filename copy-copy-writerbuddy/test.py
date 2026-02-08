import subprocess
import time
import sys
import shutil
import pyatspi

# ---------------- CONFIG ----------------
INKSCAPE_WAIT = 30
AXIDRAW_WAIT = 20

# ---------------- HELPERS ----------------
def wait_for_app(name, timeout):
    for _ in range(timeout):
        desktop = pyatspi.Registry.getDesktop(0)
        for app in desktop:
            if app.name and name.lower() in app.name.lower():
                return app
        time.sleep(1)
    return None

def find_menu_item(acc, text):
    try:
        if (
            "menu item" in acc.getRoleName().lower()
            and acc.name
            and text.lower() in acc.name.lower()
        ):
            return acc
        for i in range(acc.childCount):
            found = find_menu_item(acc.getChildAtIndex(i), text)
            if found:
                return found
    except Exception:
        pass
    return None

def find_apply_button(acc):
    try:
        if (
            acc.getRoleName().lower() == "push button"
            and acc.name
            and acc.name.lower() == "apply"
        ):
            return acc
        for i in range(acc.childCount):
            found = find_apply_button(acc.getChildAtIndex(i))
            if found:
                return found
    except Exception:
        pass
    return None

def click_accessible(acc):
    try:
        action = acc.queryAction()
        if action.nActions > 0:
            action.doAction(0)
            return True
    except Exception:
        pass

    try:
        comp = acc.queryComponent()
        x, y, w, h = comp.getExtents(pyatspi.DESKTOP_COORDS)
        subprocess.run(
            ["xdotool",
             "mousemove", str(x + w // 2), str(y + h // 2),
             "click", "1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False

# ---------------- REQUIREMENTS ----------------
if not shutil.which("inkscape") or not shutil.which("xdotool"):
    sys.exit(1)

# ---------------- LAUNCH INKSCAPE ----------------
subprocess.Popen(
    ["inkscape"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

inkscape = wait_for_app("inkscape", INKSCAPE_WAIT)
if not inkscape:
    sys.exit(1)

# ---------------- OPEN AXIDRAW CONTROL ----------------
subprocess.run(
    ["xdotool", "key", "Alt+e"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
time.sleep(1)

axidraw_menu = find_menu_item(inkscape, "axidraw")
if not axidraw_menu:
    sys.exit(1)

click_accessible(axidraw_menu)

# ---------------- WAIT FOR AXIDRAW WINDOW ----------------
axidraw_window = wait_for_app("axidraw", AXIDRAW_WAIT)
if not axidraw_window:
    sys.exit(1)

# ---------------- CLICK APPLY ----------------
apply_button = find_apply_button(axidraw_window)
if not apply_button:
    sys.exit(1)

click_accessible(apply_button)
