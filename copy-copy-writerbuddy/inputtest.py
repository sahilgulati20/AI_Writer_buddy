import svgwrite
from lxml import etree
import subprocess
import json
import os

SVG_NS = "http://www.w3.org/2000/svg"
FONT_PATH = "/home/pi/Desktop/writerbuddy/EMSDelight.svg"
OUTPUT_SVG = "output_a4.svg"
STATE_FILE = "text_state.json"

PAGE_WIDTH = 210
PAGE_HEIGHT = 297
MARGIN = 15
TEXT_HEIGHT_MM = 6
LINE_SPACING = 6 

def load_svg_font(svg_font_path):
    tree = etree.parse(svg_font_path)
    root = tree.getroot()
    font_face = root.find(".//{%s}font-face" % SVG_NS)
    glyphs = {}
    for g in root.findall(".//{%s}glyph" % SVG_NS):
        char = g.get("unicode")
        path_data = g.get("d")
        if char and path_data:
            glyphs[char] = (path_data, float(g.get("horiz-adv-x", 1000)))
    return glyphs, float(font_face.get("units-per-em", 1000)), float(font_face.get("ascent", 1000))

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f).get('current_y', MARGIN + TEXT_HEIGHT_MM)
        except:
            pass
    return MARGIN + TEXT_HEIGHT_MM

def save_state(y):
    with open(STATE_FILE, 'w') as f:
        json.dump({'current_y': y}, f)

def text_to_svg(lines):
    glyphs, units_per_em, ascent = load_svg_font(FONT_PATH)
    scale = TEXT_HEIGHT_MM / units_per_em
    dwg = svgwrite.Drawing(OUTPUT_SVG, size=(f"{PAGE_WIDTH}mm", f"{PAGE_HEIGHT}mm"))
    y = load_state()
    
    for line in lines:
        x = MARGIN
        for char in line:
            if char == " ":
                x += TEXT_HEIGHT_MM * 0.6
                continue
            if char not in glyphs:
                continue
            path_data, adv = glyphs[char]
            dwg.add(dwg.path(d=path_data, stroke="black", fill="none", stroke_width=0.5/25.4,
                           transform=f"matrix({scale} 0 0 {-scale} {x} {y + (ascent * scale)})"))
            x += adv * scale
        y += TEXT_HEIGHT_MM * LINE_SPACING
        if y > PAGE_HEIGHT - MARGIN:
            y = MARGIN + TEXT_HEIGHT_MM
    
    save_state(y)
    dwg.save()
    subprocess.Popen(["inkscape", OUTPUT_SVG])

if __name__ == "__main__":
    lines = []
    print("Enter lines (empty line to finish):")
    text_to_svg(str(input("Enter text: ")).splitlines())