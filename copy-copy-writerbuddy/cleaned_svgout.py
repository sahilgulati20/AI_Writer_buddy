import svgwrite
from lxml import etree
import json
import os

SVG_NS = "http://www.w3.org/2000/svg"

# --- FILES ---
FONT_PATH = "/home/pi/Desktop/writerbuddy/EMSDelight.svg"
OUTPUT_SVG = "output_a4.svg"
STATE_FILE = "text_state.json"

# --- PAGE SETUP (mm) ---
PAGE_WIDTH = 210
PAGE_HEIGHT = 297
MARGIN = 15
MAX_LINE_WIDTH = 180

# --- TEXT SETUP ---
TEXT_HEIGHT_MM = 6
LINE_SPACING = 1.4

START_X = MARGIN
START_Y = MARGIN + TEXT_HEIGHT_MM


def load_svg_font(svg_font_path):
    """Extract glyphs and metrics from SVG font file."""
    tree = etree.parse(svg_font_path)
    root = tree.getroot()

    font = root.find(".//{%s}font" % SVG_NS)
    font_face = root.find(".//{%s}font-face" % SVG_NS)

    units_per_em = float(font_face.get("units-per-em", 1000))
    ascent = float(font_face.get("ascent", units_per_em))
    horiz_adv_x_default = float(font.get("horiz-adv-x", units_per_em))

    glyphs = {}
    for g in root.findall(".//{%s}glyph" % SVG_NS):
        char = g.get("unicode")
        path_data = g.get("d")
        adv = float(g.get("horiz-adv-x", horiz_adv_x_default))

        if char and path_data:
            glyphs[char] = (path_data, adv)

    return glyphs, units_per_em, ascent


def load_state():
    """Load the current Y position from state file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                return state.get('current_y', START_Y)
        except:
            return START_Y
    return START_Y


def save_state(current_y):
    """Save the current Y position to state file."""
    with open(STATE_FILE, 'w') as f:
        json.dump({'current_y': current_y}, f)


def reset_state():
    """Reset the Y position to the start."""
    save_state(START_Y)


def wrap_text_to_width(text, glyphs, units_per_em, text_height_mm, max_width):
    """Wrap text to fit within max_width, breaking at word boundaries."""
    scale = text_height_mm / units_per_em
    space_width = text_height_mm * 0.6
    
    words = text.split()
    lines = []
    current_line = ""
    current_width = 0
    
    for word in words:
        word_width = 0
        for char in word:
            if char in glyphs:
                adv = glyphs[char][1]
                word_width += adv * scale
        
        if current_line:
            word_width += space_width
        
        if current_width + word_width <= max_width:
            if current_line:
                current_line += " " + word
                current_width += space_width
            else:
                current_line = word
            current_width += word_width - (space_width if current_line != word else 0)
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            current_width = word_width - space_width if word_width > space_width else word_width
    
    if current_line:
        lines.append(current_line)
    
    return lines


def text_to_svg(lines, output_file=OUTPUT_SVG):
    """Convert text lines to SVG using font glyphs."""
    glyphs, units_per_em, ascent = load_svg_font(FONT_PATH)

    scale = TEXT_HEIGHT_MM / units_per_em
    stroke_width_in = 0.5 / 25.4

    dwg = svgwrite.Drawing(
        output_file,
        size=(f"{PAGE_WIDTH}mm", f"{PAGE_HEIGHT}mm"),
        viewBox=f"0 0 {PAGE_WIDTH} {PAGE_HEIGHT}",
        profile="tiny",
    )

    main_g = dwg.g(id="text_group", fill="none", stroke="black", stroke_linecap="round", stroke_linejoin="round")

    wrapped_lines = []
    for line in lines:
        wrapped_lines.extend(wrap_text_to_width(line, glyphs, units_per_em, TEXT_HEIGHT_MM, MAX_LINE_WIDTH))

    y = load_state()
    final_y = y

    for line in wrapped_lines:
        x = START_X

        for char in line:
            if char == " ":
                x += TEXT_HEIGHT_MM * 0.6
                continue

            if char not in glyphs:
                continue

            path_data, adv = glyphs[char]

            matrix_a = scale
            matrix_d = -scale
            matrix_e = x
            matrix_f = y + (ascent * scale)

            main_g.add(
                dwg.path(
                    d=path_data,
                    stroke_width=stroke_width_in,
                    transform=f"matrix({matrix_a} 0 0 {matrix_d} {matrix_e} {matrix_f})",
                )
            )

            x += adv * scale

        y += TEXT_HEIGHT_MM * LINE_SPACING
        final_y = y

        if y > PAGE_HEIGHT - MARGIN:
            y = START_Y

    save_state(final_y)

    dwg.add(main_g)
    dwg.save()
    print(f"Saved SVG as: {output_file}")
