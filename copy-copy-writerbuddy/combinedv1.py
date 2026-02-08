import subprocess
import time
import sys

import pyatspi
import cleaned_svgout


# ==========================================================
# 1. GENERATE SVG
# ==========================================================
SVG_FILE = "output_1a4.svg"

cleaned_svgout.text_to_svg(
    ["Hello, World!", "This is a test of the cleaned SVG output module."],
    output_file=SVG_FILE
)

print(f"SVG generated: {SVG_FILE}")


# ==========================================================
# 2. OPEN SVG IN INKSCAPE
# ==========================================================
subprocess.Popen(
    ["inkscape", SVG_FILE],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)


# ==========================================================
# 3. WAIT FOR INKSCAPE APP
# ==========================================================
inkscape_app = None
for _ in range(30):
    desktop = pyatspi.Registry.getDesktop(0)
    for app in desktop:
        if app.name and "inkscape" in app.name.lower():
            inkscape_app = app
            break
    if inkscape_app:
        break
    time.sleep(1)

if not inkscape_app:
    print("Inkscape not found")
    sys.exit(1)

print("Inkscape detected")


# ==========================================================
# 4. OPEN EXTENSIONS MENU
# ==========================================================
subprocess.run(["xdotool", "key", "Alt+e"], check=False)
time.sleep(1)


# ==========================================================
# 5. FIND AXIDRAW MENU ITEM
# ==========================================================
def find_axidraw(acc):
    try:
        if (
            "menu item" in (acc.getRoleName() or "").lower()
            and acc.name
            and "axidraw" in acc.name.lower()
        ):
            return acc
        for i in range(acc.childCount):
            found = find_axidraw(acc.getChildAtIndex(i))
            if found:
                return found
    except Exception:
        pass
    return None


axidraw_item = find_axidraw(inkscape_app)
if not axidraw_item:
    print("AxiDraw menu item not found")
    sys.exit(1)


# ==========================================================
# 6. CLICK AXIDRAW MENU
# ==========================================================
try:
    axidraw_item.queryAction().doAction(0)
except Exception:
    comp = axidraw_item.queryComponent()
    x, y, w, h = comp.getExtents(pyatspi.DESKTOP_COORDS)
    subprocess.run(
        ["xdotool", "mousemove", str(x + w // 2), str(y + h // 2), "click", "1"],
        check=False
    )

print("AxiDraw Control opened")


# ==========================================================
# 7. WAIT FOR AXIDRAW CONTROL WINDOW
# ==========================================================
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

print("AxiDraw window detected")


# ==========================================================
# 8. FIND & CLICK APPLY
# ==========================================================
def find_apply(acc):
    try:
        role = (acc.getRoleName() or "").lower()
        name = (acc.name or "").strip().lower()

        if "button" in role and name == "apply":
            return acc

        for i in range(acc.childCount):
            found = find_apply(acc.getChildAtIndex(i))
            if found:
                return found
    except Exception:
        pass
    return None


def click_accessible(acc):
    try:
        action = acc.queryAction()
        for i in range(action.nActions):
            if action.getName(i).lower() in ("click", "press"):
                action.doAction(i)
                return True
    except Exception:
        pass

    try:
        comp = acc.queryComponent()
        x, y, w, h = comp.getExtents(pyatspi.DESKTOP_COORDS)
        subprocess.run(
            ["xdotool", "mousemove", str(x + w // 2), str(y + h // 2), "click", "1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        return True
    except Exception:
        return False


apply_btn = find_apply(axidraw_window)
if apply_btn and click_accessible(apply_btn):
    print("Apply button clicked")
else:
    print("Failed to click Apply button")


# ==========================================================
# 9. OPTIONAL: DUMP AXIDRAW UI (DEBUG)
# ==========================================================
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
