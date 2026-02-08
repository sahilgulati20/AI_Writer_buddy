# axidraw_plot.py
import subprocess
import time
import sys
import pyatspi


def plot(filename, inkscape_timeout=30, axidraw_timeout=20):
    """
    Open an SVG in Inkscape, open AxiDraw Control, and click Apply.
    """

    # --------------------------------------------------
    # 1. OPEN FILE IN INKSCAPE
    # --------------------------------------------------
    subprocess.Popen(
        ["inkscape", filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # --------------------------------------------------
    # 2. WAIT FOR INKSCAPE
    # --------------------------------------------------
    inkscape_app = None
    for _ in range(inkscape_timeout):
        desktop = pyatspi.Registry.getDesktop(0)
        for app in desktop:
            if app.name and "inkscape" in app.name.lower():
                inkscape_app = app
                break
        if inkscape_app:
            break
        time.sleep(1)

    if not inkscape_app:
        raise RuntimeError("Inkscape not found")

    # --------------------------------------------------
    # 3. OPEN EXTENSIONS MENU
    # --------------------------------------------------
    # subprocess.run(["xdotool", "key", "Alt+e"], check=False)
    # time.sleep(1)

    # --------------------------------------------------
    # 4. FIND AXIDRAW MENU ITEM
    # --------------------------------------------------
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
        raise RuntimeError("AxiDraw menu item not found")

    # --------------------------------------------------
    # 5. CLICK AXIDRAW
    # --------------------------------------------------
    try:
        axidraw_item.queryAction().doAction(0)
    except Exception:
        comp = axidraw_item.queryComponent()
        x, y, w, h = comp.getExtents(pyatspi.DESKTOP_COORDS)
        subprocess.run(
            ["xdotool", "mousemove", str(x + w // 2), str(y + h // 2), "click", "1"],
            check=False,
        )

    # --------------------------------------------------
    # 6. WAIT FOR AXIDRAW WINDOW
    # --------------------------------------------------
    axidraw_window = None
    for _ in range(axidraw_timeout):
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
        raise RuntimeError("AxiDraw Control window not found")

    # --------------------------------------------------
    # 7. FIND & CLICK APPLY
    # --------------------------------------------------
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

    def click(acc):
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
                check=False,
            )
            return True
        except Exception:
            return False

    apply_btn = find_apply(axidraw_window)
    if not apply_btn or not click(apply_btn):
        raise RuntimeError("Failed to click Apply")

    return True
