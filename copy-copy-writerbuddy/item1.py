import subprocess
import time
import sys

import pyatspi

# ---------- WAIT FOR AXIDRAW CONTROL WINDOW ----------
axidraw_window = None
for _ in range(20):
    desktop = pyatspi.Registry.getDesktop(0)
    for app in desktop:
        for i in range(app.childCount):
            win = app.getChildAtIndex(i)
            if win.name and "axidraw" in win.name.lower():
                axidraw_window = win
                break
        if axidraw_window:
            break
    if axidraw_window:
        break
    time.sleep(1)

if not axidraw_window:
    print("AxiDraw Control window not found")
    sys.exit(1)

# ---------- FIND AND CLICK APPLY BUTTON ----------
def find_apply_button(acc):
    try:
        role = acc.getRoleName().lower() if acc.getRoleName() else ""
        if (
            "button" in role
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
            ["xdotool", "mousemove", str(x + w // 2), str(y + h // 2), "click", "1"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False

axidraw_item = find_axidraw(inkscape_app)
if not axidraw_item:
    sys.exit(1)

# ---------- CLICK AXIDRAW ----------
try:
    axidraw_item.queryAction().doAction(0)
except Exception:
    comp = axidraw_item.queryComponent()
    x, y, w, h = comp.getExtents(pyatspi.DESKTOP_COORDS)
    subprocess.run(
        ["xdotool", "mousemove", str(x + w // 2), str(y + h // 2), "click", "1"],
        check=False
    )

# ---------- WAIT FOR AXIDRAW CONTROL WINDOW ----------
axidraw_window = None
for _ in range(20):
    desktop = pyatspi.Registry.getDesktop(0)
    for app in desktop:
        for i in range(app.childCount):
            win = app.getChildAtIndex(i)
            if win.name and "axidraw" in win.name.lower():
                axidraw_window = win
                break
        if axidraw_window:
            break
    if axidraw_window:
        break
    time.sleep(1)

if not axidraw_window:
    print("AxiDraw Control window not found")
    sys.exit(1)

# ---------- FIND AND CLICK APPLY ----------
apply_button = find_apply_button(axidraw_window)
if apply_button:
    clicked = click_accessible(apply_button)
    if clicked:
        print("Apply button clicked")
    else:
        print("Failed to click Apply button")
else:
    print("Apply button not found")

# ---------- PRINT ALL OPTIONS ----------
def dump_elements(acc, indent=0):
    try:
        role = acc.getRoleName()
        name = acc.name or ""
        if name:
            print(" " * indent + f"[{role}] {name}")
        for i in range(acc.childCount):
            dump_elements(acc.getChildAtIndex(i), indent + 2)
    except Exception:
        pass

print("\n=== AXIDRAW CONTROL OPTIONS ===\n")
dump_elements(axidraw_window)
