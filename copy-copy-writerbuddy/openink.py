#!/usr/bin/env python3
"""
openink.py

Launch Inkscape and click the Extensions menu. Two modes:
 - calibrate: record the screen coordinates of the Extensions menu
 - click: launch Inkscape then move+click the recorded coordinates

Usage:
  python openink.py calibrate
  python openink.py click

Requirements:
  pip install pyautogui

Notes:
 - Coordinates are saved to `ink_coords.json` in the same folder.
 - If coordinates aren't set, run the `calibrate` mode first.
"""

import argparse
import json
import os
import subprocess
import sys
import time

try:
    import pyautogui
except Exception as e:
    print("pyautogui is required. Install with: pip install pyautogui")
    print("Error import pyautogui:", e)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
COORDS_FILE = os.path.join(SCRIPT_DIR, 'ink_coords.json')


def save_coords(x, y):
    data = {'x': x, 'y': y}
    with open(COORDS_FILE, 'w') as f:
        json.dump(data, f)


def load_coords():
    if not os.path.exists(COORDS_FILE):
        return None
    with open(COORDS_FILE, 'r') as f:
        return json.load(f)


def calibrate():
    print('\nCalibrate mode:')
    print(' - Move your mouse pointer over the Inkscape "Extensions" menu item,')
    print('   then press Enter here to record the position.')
    input('Press Enter when ready...')
    x, y = pyautogui.position()
    save_coords(x, y)
    print(f'Saved coordinates: x={x}, y={y} -> {COORDS_FILE}')


def launch_inkscape(wait=5, focus_delay=0.5):
    try:
        subprocess.Popen(['inkscape'])
    except FileNotFoundError:
        print('Could not find `inkscape` in PATH. Please install Inkscape or ensure it is in your PATH.')
        sys.exit(1)
    # Give the app time to open
    for i in range(wait):
        print(f'Waiting for Inkscape to open... {wait-i}s', end='\r')
        time.sleep(1)
    print(' ' * 60, end='\r')
    time.sleep(focus_delay)


def click_extensions(coords, clicks=1, interval=0.25):
    x = coords['x']
    y = coords['y']
    print(f'Moving to x={x}, y={y} and clicking...')
    pyautogui.moveTo(x, y, duration=0.3)
    pyautogui.click(x, y, clicks=clicks, interval=interval)
    print('Click sent.')


def focus_inkscape():
    # Try to focus Inkscape window using multiple methods
    # 1) try pygetwindow (shipped as part of pyautogui on some installs)
    try:
        import pygetwindow as gw
        wins = gw.getWindowsWithTitle('Inkscape')
        if wins:
            wins[0].activate()
            time.sleep(0.3)
            return True
    except Exception:
        pass

    # 2) try xdotool
    try:
        proc = subprocess.run(['which', 'xdotool'], capture_output=True)
        if proc.returncode == 0:
            # find window by class or name
            search = subprocess.run(['xdotool', 'search', '--onlyvisible', '--class', 'Inkscape'], capture_output=True, text=True)
            winids = [w for w in search.stdout.split() if w.strip()]
            if winids:
                subprocess.run(['xdotool', 'windowactivate', '--sync', winids[0]])
                time.sleep(0.3)
                return True
    except Exception:
        pass

    return False


def send_hotkeys(seq):
    # seq: comma-separated combos like 'alt+e,down,enter'
    parts = [s.strip() for s in seq.split(',') if s.strip()]
    for token in parts:
        combo = [k.strip() for k in token.split('+') if k.strip()]
        if not combo:
            continue
        try:
            pyautogui.hotkey(*combo)
        except Exception:
            # fallback: press keys individually
            for k in combo:
                pyautogui.press(k)
        time.sleep(0.25)


def access_menu_atspi(menu_path, timeout=6):
    """Use AT-SPI (pyatspi) to find Inkscape and activate a menu path like "Extensions>Render>Particles".

    Returns True on success, False otherwise.
    """
    try:
        import pyatspi
    except Exception as e:
        print('pyatspi is required for AT-SPI access. Install system package at-spi2-core and python bindings (e.g., at-spi2-python).')
        print('Import error:', e)
        return False

    # Give accessibility registry time to populate
    end = time.time() + timeout
    desktop = None
    while time.time() < end:
        try:
            desktop = pyatspi.Registry.getDesktop(0)
            if desktop:
                break
        except Exception:
            time.sleep(0.3)
    if not desktop:
        print('Could not access AT-SPI desktop.')
        return False

    # find Inkscape application object
    app_obj = None
    for i in range(desktop.childCount):
        try:
            child = desktop.getChildAtIndex(i)
            if child and child.name and 'inkscape' in child.name.lower():
                app_obj = child
                break
        except Exception:
            continue
    if not app_obj:
        print('Inkscape application not found via AT-SPI.')
        return False

    parts = [p.strip() for p in menu_path.split('>') if p.strip()]

    def find_child_by_name(parent, name):
        lname = name.lower()
        for j in range(parent.childCount):
            try:
                c = parent.getChildAtIndex(j)
                if c and c.name and c.name.strip().lower() == lname:
                    return c
            except Exception:
                continue
        return None

    current = app_obj
    for part in parts:
        # try direct children first
        found = find_child_by_name(current, part)
        if not found:
            # fallback: deep search
            def deep_search(obj):
                candidate = find_child_by_name(obj, part)
                if candidate:
                    return candidate
                for k in range(obj.childCount):
                    try:
                        c = obj.getChildAtIndex(k)
                        res = deep_search(c)
                        if res:
                            return res
                    except Exception:
                        continue
                return None
            found = deep_search(current)
        if not found:
            print(f'Menu part "{part}" not found via AT-SPI.')
            return False

        # activate the found object (try action interface)
        try:
            action = found.queryAction()
            if action and action.nActions > 0:
                found.doAction(0)
            else:
                # try to focus/press it via keyboard alternatives
                try:
                    found.grabFocus()
                except Exception:
                    pass
        except Exception:
            try:
                found.doAction(0)
            except Exception:
                pass

        # small delay for submenu to appear
        time.sleep(0.4)
        current = found

    return True


def detect_accessible_under_mouse_or_focus():
    """Return a short description of the accessible object under the mouse, or the focused object.

    Best-effort: uses pyatspi if available, otherwise falls back to xdotool window title.
    """
    try:
        import pyatspi
    except Exception:
        # fallback to xdotool window title
        try:
            name = subprocess.check_output(['xdotool', 'getwindowfocus', 'getwindowname'], text=True).strip()
            return f'Window title (xdotool): {name}'
        except Exception:
            return 'No AT-SPI and xdotool not available; cannot detect element.'

    # get mouse position
    x, y = pyautogui.position()

    try:
        desktop = pyatspi.Registry.getDesktop(0)
    except Exception:
        return 'Could not access AT-SPI desktop.'

    def contains_point(comp, px, py):
        try:
            c = comp.queryComponent()
            x0, y0, w, h = c.getExtents(pyatspi.DESKTOP_COORDS)
            return (px >= x0 and px <= x0 + w and py >= y0 and py <= y0 + h)
        except Exception:
            return False

    def deep_find(parent):
        # find deepest child that contains point
        for i in range(parent.childCount):
            try:
                child = parent.getChildAtIndex(i)
            except Exception:
                continue
            if contains_point(child, x, y):
                deeper = deep_find(child)
                return deeper or child
        return None

    # Search apps/windows
    for i in range(desktop.childCount):
        try:
            app = desktop.getChildAtIndex(i)
        except Exception:
            continue
        if contains_point(app, x, y):
            found = deep_find(app)
            target = found or app
            try:
                name = getattr(target, 'name', '')
                role = getattr(target, 'roleName', '')
                desc = getattr(target, 'description', '')
                return f'AT-SPI: name="{name}", role="{role}", description="{desc}"'
            except Exception:
                return 'Found an accessible object but could not read properties.'

    # If nothing under mouse, try focused object
    try:
        # traverse to find focused object
        def find_focused(parent):
            for i in range(parent.childCount):
                try:
                    c = parent.getChildAtIndex(i)
                except Exception:
                    continue
                try:
                    state = c.getState()
                    sstr = str(state)
                    if 'focused' in sstr.lower():
                        return c
                except Exception:
                    pass
                res = find_focused(c)
                if res:
                    return res
            return None

        focused_obj = find_focused(desktop)
        if focused_obj:
            name = getattr(focused_obj, 'name', '')
            role = getattr(focused_obj, 'roleName', '')
            desc = getattr(focused_obj, 'description', '')
            return f'Focused AT-SPI object: name="{name}", role="{role}", description="{desc}"'
    except Exception:
        pass

    return 'No accessible object found under mouse or focus.'


def list_accessible_items(app_name='Inkscape', role_filter=None, max_depth=2):
    """Return a list of strings describing accessible items for the given app.

    If AT-SPI isn't available, returns an empty list.
    """
    try:
        import pyatspi
    except Exception:
        print('pyatspi not available; cannot list accessible items. Install AT-SPI Python bindings.')
        return []

    try:
        desktop = pyatspi.Registry.getDesktop(0)
    except Exception:
        print('Could not access AT-SPI desktop.')
        return []

    target_app = None
    name_lower = app_name.lower()
    for i in range(desktop.childCount):
        try:
            child = desktop.getChildAtIndex(i)
        except Exception:
            continue
        if child and child.name and name_lower in child.name.lower():
            target_app = child
            break

    if not target_app:
        print(f'Application matching "{app_name}" not found via AT-SPI.')
        return []

    results = []

    def repr_obj(obj, prefix=''):
        try:
            name = getattr(obj, 'name', '') or ''
            role = getattr(obj, 'roleName', '') or ''
            desc = getattr(obj, 'description', '') or ''
            return f"{prefix}{role}: '{name}' -- {desc}".strip()
        except Exception:
            return f"{prefix}{obj}".strip()

    def traverse(obj, depth, prefix=''):
        if depth < 0:
            return
        try:
            r = repr_obj(obj, prefix)
            if role_filter:
                if role_filter.lower() in str(getattr(obj, 'roleName', '') or '').lower() or role_filter.lower() in (getattr(obj, 'name', '') or '').lower():
                    results.append(r)
            else:
                results.append(r)
        except Exception:
            pass
        try:
            for j in range(obj.childCount):
                try:
                    c = obj.getChildAtIndex(j)
                except Exception:
                    continue
                traverse(c, depth-1, prefix + '  ')
        except Exception:
            pass

    traverse(target_app, max_depth)
    return results


def main():
    parser = argparse.ArgumentParser(description='Open Inkscape and click Extensions menu')
    sub = parser.add_subparsers(dest='command')

    parser_cal = sub.add_parser('calibrate', help='Record mouse position for Extensions menu')

    parser_click = sub.add_parser('click', help='Launch Inkscape and click recorded position')
    parser_click.add_argument('--delay', '-d', type=int, default=6, help='Seconds to wait for Inkscape to open')
    parser_click.add_argument('--clicks', type=int, default=1, help='Number of clicks to send')

    parser_hot = sub.add_parser('hotkey', help='Launch Inkscape and send menu hotkeys (no coords/images)')
    parser_hot.add_argument('--keys', '-k', default='alt+e', help='Hotkey sequence, comma-separated combos e.g. "alt+e,down,enter"')
    parser_hot.add_argument('--delay', '-d', type=int, default=6, help='Seconds to wait for Inkscape to open')

    parser_access = sub.add_parser('access', help='Launch Inkscape and activate a menu item by name via AT-SPI')
    parser_access.add_argument('--menu', '-m', default='Extensions', help='Menu path, use ">" to separate nested menus, e.g. "Extensions>Render>Particles"')
    parser_access.add_argument('--delay', '-d', type=int, default=6, help='Seconds to wait for Inkscape to open')

    parser_preset = sub.add_parser('preset', help='Launch Inkscape and run preset sequence: Alt+N, wait, downs, Enter')
    parser_preset.add_argument('--delay', '-d', type=int, default=6, help='Seconds to wait for Inkscape to open')
    parser_preset.add_argument('--wait', '-w', type=float, default=1.0, help='Seconds to wait after Alt+N')
    parser_preset.add_argument('--downs', type=int, default=4, help='How many Down presses before Enter')
    parser_preset.add_argument('--report', action='store_true', help='After preset, report what was clicked (uses AT-SPI)')

    parser_list = sub.add_parser('list', help='List accessible UI items for an application (default: Inkscape)')
    parser_list.add_argument('--app', '-a', default='Inkscape', help='Application name to search for (case-insensitive)')
    parser_list.add_argument('--role', '-r', default=None, help='Optional role filter (e.g., "menu", "menu bar", "toolbar")')
    parser_list.add_argument('--depth', '-D', type=int, default=2, help='Depth to traverse for listing children')

    parser_capture = sub.add_parser('capture', help='Take a screenshot for creating an image template')
    parser_capture.add_argument('--out', '-o', default='extensions_template.png', help='Output file for screenshot/template')

    parser_click_image = sub.add_parser('click-image', help='Launch Inkscape and click a saved image template')
    parser_click_image.add_argument('--image', '-i', default='extensions_template.png', help='Image file to locate on screen')
    parser_click_image.add_argument('--confidence', '-c', type=float, default=0.9, help='confidence for image match (0-1)')
    parser_click_image.add_argument('--delay', '-d', type=int, default=6, help='Seconds to wait for Inkscape to open')
    parser_click_image.add_argument('--clicks', type=int, default=1, help='Number of clicks to send')

    args = parser.parse_args()

    if args.command == 'calibrate':
        calibrate()
        return

    if args.command == 'capture':
        out = args.out
        print(f'Taking screenshot and saving to {out}...')
        img = pyautogui.screenshot()
        img.save(out)
        print('Saved. You can crop this file to a small template image (e.g., the Extensions menu text) and use it with `click-image`.')
        return

    if args.command == 'hotkey':
        keys = args.keys
        launch_inkscape(wait=args.delay)
        focused = focus_inkscape()
        if not focused:
            print('Could not programmatically focus Inkscape. Make sure the window is visible; sending keys anyway.')
        print(f'Sending hotkeys: {keys}')
        send_hotkeys(keys)
        print('Hotkeys sent.')
        return

    if args.command == 'access':
        menu = args.menu
        launch_inkscape(wait=args.delay)
        focused = focus_inkscape()
        if not focused:
            print('Warning: could not focus Inkscape window automatically. Ensure it is visible for AT-SPI to find it.')
        print(f'Attempting to activate menu path: {menu}')
        ok = access_menu_atspi(menu)
        if ok:
            print('Menu activated via AT-SPI.')
        else:
            print('Failed to activate menu via AT-SPI.')
        return

    if args.command == 'preset':
        launch_inkscape(wait=args.delay)
        focused = focus_inkscape()
        if not focused:
            print('Warning: could not focus Inkscape window automatically. Make sure it is visible; keys will still be sent.')
        print('Sending Alt+N...')
        try:
            pyautogui.hotkey('alt', 'n')
        except Exception:
            pyautogui.keyDown('alt')
            pyautogui.press('n')
            pyautogui.keyUp('alt')
        time.sleep(args.wait)
        for i in range(args.downs):
            pyautogui.press('down')
            time.sleep(0.12)
        pyautogui.press('enter')
        print('Preset sequence complete.')
        if getattr(args, 'report', False):
            print('Reporting accessible element under mouse / focused object:')
            info = detect_accessible_under_mouse_or_focus()
            print(info)
        return

    if args.command == 'list':
        app_name = args.app
        role = args.role
        depth = args.depth
        print(f'Listing accessible items for app "{app_name}" (role filter: {role}, depth: {depth})')
        items = list_accessible_items(app_name, role_filter=role, max_depth=depth)
        if not items:
            print('No accessible items found or AT-SPI unavailable.')
        else:
            for line in items:
                print(line)
        return

    if args.command == 'click':
        coords = load_coords()
        if coords is None:
            print('No coordinates found. Run `python openink.py calibrate` first to record the Extensions menu location.')
            sys.exit(1)
        launch_inkscape(wait=args.delay)
        click_extensions(coords, clicks=args.clicks)
        return

    if args.command == 'click-image':
        imgfile = args.image
        if not os.path.exists(imgfile):
            print(f'Image file {imgfile} not found. Run `python openink.py capture` and crop a template image first.')
            sys.exit(1)
        launch_inkscape(wait=args.delay)
        print(f'Locating image {imgfile} on screen...')
        # Try multiple attempts to allow UI to settle
        found = None
        for attempt in range(6):
            try:
                # pyautogui.locateCenterOnScreen supports confidence when OpenCV is installed
                center = pyautogui.locateCenterOnScreen(imgfile, confidence=args.confidence)
            except TypeError:
                # Older pyautogui without confidence support
                center = pyautogui.locateCenterOnScreen(imgfile)
            if center:
                found = center
                break
            time.sleep(0.8)
        if not found:
            print('Could not find image on screen. Try increasing confidence or recapturing a clearer template.')
            sys.exit(1)
        x, y = found
        print(f'Found at x={x}, y={y}; clicking...')
        pyautogui.moveTo(x, y, duration=0.3)
        pyautogui.click(x, y, clicks=args.clicks)
        print('Click sent.')
        return

    parser.print_help()


if __name__ == '__main__':
    main()
