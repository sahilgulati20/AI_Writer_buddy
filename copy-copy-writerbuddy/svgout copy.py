import random
import svgwrite
from lxml import etree
import subprocess

SVG_NS = "http://www.w3.org/2000/svg"

# --- FILES ---
FONT_PATH = "/home/pi/Desktop/writerbuddy/EMSDelight.svg"
OUTPUT_SVG = "output_a4.svg"

# --- PAGE SETUP (mm) ---
PAGE_WIDTH = 210
PAGE_HEIGHT = 297
MARGIN = 15
MAX_LINE_WIDTH = 180

# --- TEXT SETUP ---
TEXT_HEIGHT_MM = 6
LINE_SPACING = 1.4   # multiplier

START_X = MARGIN
START_Y = MARGIN + TEXT_HEIGHT_MM

WORDS = [
    "CNC", "PLOTTER", "SINGLE", "STROKE", "VECTOR",
    "LASER", "ENGRAVE", "PATH", "SVG", "HERSHEY",
    "OPEN", "LINES", "NO", "OUTLINES", "PURE"
]


def random_line():
    return " ".join(random.choice(WORDS) for _ in range(random.randint(3, 6)))


def load_svg_font(svg_font_path):
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


def wrap_text_to_width(text, glyphs, units_per_em, text_height_mm, max_width):
    """Wrap text to fit within max_width, breaking at word boundaries."""
    scale = text_height_mm / units_per_em
    space_width = text_height_mm * 0.6
    
    words = text.split()
    lines = []
    current_line = ""
    current_width = 0
    
    for word in words:
        # Calculate word width
        word_width = 0
        for char in word:
            if char in glyphs:
                adv = glyphs[char][1]
                word_width += adv * scale
        
        # Add space before word if not first word
        if current_line:
            word_width += space_width
        
        # Check if word fits on current line
        if current_width + word_width <= max_width:
            if current_line:
                current_line += " " + word
                current_width += space_width
            else:
                current_line = word
            current_width += word_width - (space_width if current_line != word else 0)
        else:
            # Start new line
            if current_line:
                lines.append(current_line)
            current_line = word
            current_width = word_width - space_width if word_width > space_width else word_width
    
    if current_line:
        lines.append(current_line)
    
    return lines


def text_to_svg(lines):
    glyphs, units_per_em, ascent = load_svg_font(FONT_PATH)

    scale = TEXT_HEIGHT_MM / units_per_em
    stroke_width_in = 0.5 / 25.4  # 0.5mm converted to inches

    dwg = svgwrite.Drawing(
        OUTPUT_SVG,
        size=(f"{PAGE_WIDTH}mm", f"{PAGE_HEIGHT}mm"),
        viewBox=f"0 0 {PAGE_WIDTH} {PAGE_HEIGHT}",
        profile="tiny",
    )

    # Create main group with common stroke properties
    main_g = dwg.g(id="text_group", fill="none", stroke="black", stroke_linecap="round", stroke_linejoin="round")

    # Pre-wrap all text lines to fit within max width
    wrapped_lines = []
    for line in lines:
        wrapped_lines.extend(wrap_text_to_width(line, glyphs, units_per_em, TEXT_HEIGHT_MM, MAX_LINE_WIDTH))

    y = START_Y

    for line in wrapped_lines:
        x = START_X

        for char in line:
            if char == " ":
                x += TEXT_HEIGHT_MM * 0.6
                continue

            if char not in glyphs:
                continue

            path_data, adv = glyphs[char]

            # Create matrix transform: scale and translate
            # Matrix format: matrix(a c e b d f) = [a c e; b d f; 0 0 1]
            # We want: translate(x,y) then scale(scale, -scale) then translate(0, -ascent)
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

        # stop if we hit bottom margin
        if y > PAGE_HEIGHT - MARGIN:
            break

    dwg.add(main_g)
    dwg.save()
    print(f"Saved A4 SVG as: {OUTPUT_SVG}")
    
    # Open in Inkscape
    subprocess.Popen(["inkscape", OUTPUT_SVG])


if __name__ == "__main__":
    lines = [random_line() for _ in range(5)]

    print("Generated text:")
    for l in lines:
        print(" ", l)

    text_to_svg(lines)
