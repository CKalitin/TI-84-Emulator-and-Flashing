"""Home-screen OCR for the TI-84 Plus large font (16 cols x 8 rows of 6x8 cells).

The glyph table (font.json) is calibrated from the emulator itself: a
program Output()s every character at a known cell, and we record the bitmap.
Run `python ocr.py` to (re)build it.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(HERE, "font.json")

CHARSET = ("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz"
           "!#$%&'()*+,-./:;<=>?[]{}^_|@θ≠≤≥²³∠ᴇ⁻ᵀ")

_font = None


def cell_bits(px, row, col, dx=0, dy=0):
    """48-char '0'/'1' string for one 6x8 cell (row 0-7, col 0-15),
    optionally shifted dx pixels horizontally."""
    def pix(x, y):
        x += col * 6 + dx
        y += row * 8 + dy
        return 0 <= x < 96 and 0 <= y < 64 and px[y * 96 + x]
    return "".join("1" if pix(x, y) else "0" for y in range(8) for x in range(6))


def _load():
    global _font
    if _font is None:
        with open(FONT_PATH) as f:
            _font = json.load(f)
    return _font


def read_cell(px, row, col, dx=0, dy=0):
    bits = cell_bits(px, row, col, dx, dy)
    font = _load()
    # highlighted menu items: whole cell inverted, or only its 5x7 glyph area
    inv = "".join("1" if b == "0" else "0" for b in bits)
    inv57 = "".join(("1" if b == "0" else "0") if (i % 6 < 5 and i < 42) else "0"
                    for i, b in enumerate(bits))
    for b in (bits, inv, inv57):
        if b in font:
            return font[b]
    if bits.count("1") >= 33 and bits[42:].count("1") >= 4:
        return "█"                     # cursor block
    # nearest match within a small Hamming distance (cursor/blink artefacts)
    best, bd = "?", 5
    for b in (bits, inv, inv57):
        q = int(b, 2)
        for k, v in _font_ints():
            d = (k ^ q).bit_count()
            if d < bd:
                best, bd = v, d
    return best


_ints = None


def _font_ints():
    global _ints
    if _ints is None:
        _ints = [(int(k, 2), v) for k, v in _load().items()]
    return _ints


def _read_rows(px, dy):
    lines = []
    for r in range(8):
        # Most text sits on the 6px grid, but e.g. "Done" is drawn 1px left of it.
        best = None
        for dx in (0, -1, 1):
            line = "".join(read_cell(px, r, c, dx, dy) for c in range(16)).rstrip()
            if best is None or line.count("?") < best.count("?"):
                best = line
            if "?" not in line:
                break
        lines.append(best)
    return lines


def read_screen(px):
    """Return the 8 home-screen lines (right-stripped).

    The real LCD can be vertically scrolled (row offset), so if the grid-aligned
    read has unknown glyphs, try every vertical offset and keep the best."""
    def score(lines):  # recognised glyphs minus unknown ones
        t = "".join(lines)
        return len(t.replace(" ", "").replace("?", "")) - 3 * t.count("?")

    best = _read_rows(px, 0)
    if any("?" in l for l in best):
        for dy in range(-7, 8):
            if dy:
                cand = _read_rows(px, dy)
                if score(cand) > score(best):
                    best = cand
    return best


def calibrate():
    import sys
    sys.path.insert(0, HERE)
    from tivars.models import TI_84P
    from tivars.types import TIProgram
    from ti84emu import TI84, T_PROG

    font = {" " * 0 + "0" * 48: " "}
    chars = list(CHARSET)
    calc = TI84()
    while chars:
        batch, lines = [], ["ClrHome"]
        for r in range(8):
            for c in range(15):            # skip col 16: run indicator lives there
                if chars:
                    ch = chars.pop(0)
                    batch.append((r, c, ch))
                    lines.append('Output(%d,%d,"%s")' % (r + 1, c + 1, ch))
        lines.append("Pause ")
        prog = TIProgram(name="OCRCAL")
        prog.load_string("\n".join(lines), model=TI_84P)
        calc.send_var(T_PROG, b"OCRCAL", bytes(prog.calc_data))
        calc.keys("CLEAR", "PRGM", "ENTER", "ENTER")
        calc.run(3)
        px = calc.pixels()
        for r, c, ch in batch:
            bits = cell_bits(px, r, c)
            if bits in font and font[bits] != ch:
                print("collision: %r vs %r" % (font[bits], ch))
            font.setdefault(bits, ch)
        calc.press("ENTER")       # leave Pause
        calc.run(1)
    # '"' and '→' cannot be Output() inside a string; read them from the
    # program editor instead, where the source line ':Disp "Q"' / ':1→Q' shows.
    prog = TIProgram(name="OCRCAL")
    prog.load_string('Disp "Q"\n1→Q', model=TI_84P)
    calc.send_var(T_PROG, b"OCRCAL", bytes(prog.calc_data))
    calc.keys("SECOND", "MODE", "CLEAR", "PRGM", "RIGHT", "ENTER")
    calc.run(1)
    px = calc.pixels()
    for r, c, ch in [(1, 6, '"'), (2, 2, "→")]:
        font.setdefault(cell_bits(px, r, c), ch)
    calc.keys("SECOND", "MODE")
    calc.close()
    font["0" * 48] = " "
    with open(FONT_PATH, "w") as f:
        json.dump(font, f, ensure_ascii=False, indent=0)
    print("wrote %d glyphs to %s" % (len(font), FONT_PATH))


if __name__ == "__main__":
    calibrate()
