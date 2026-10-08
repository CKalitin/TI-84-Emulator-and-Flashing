"""Emulator tests for AREAMOM.  Run: ./ti84 test programs/areamom

Reference numbers come from MECH 360 L5 §4 / L6 §3 (L-channel) and L5 §5
(Z section). Everything else is checked against `reference()` below, which
implements the L5 §3.4 formulas independently of the program.
"""
import math
import random
import re

from ti84emu import (decode_list, decode_matrix, decode_real, matrix_data, tifloat_encode,
                     T_LIST, T_MATRIX, T_REAL)

MAT_I = b"\x5c\x08"
# OCR can't read Δ, ₀, Σ, β or ° (they come out as '?'), so match on the rest
SHAPE_LABELS = ["A=", "I_x=", "I_y=", "?x?*=", "?y?*=", "?y²A=", "?x²A=", "-?x?yA="]
TOTAL_LABELS = ["?A=", "x?*=", "y?*=", "I_x=", "I_y=", "I_xy="]
PRINC_LABELS = ["I_O=", "R=", "I_str=", "I_wk=", "?="]

L_CHANNEL = [(10, 80, 0, 35), (50, 10, 30, 0)]
Z_SECTION = [(10, 40, -40, 25), (90, 10, 0, 0), (10, 40, 40, -25)]


def num(x):
    """A number as keypresses: ~ is the (-) key, no exponent notation."""
    s = ("%.12f" % abs(x)).rstrip("0").rstrip(".") or "0"
    return ("~" if x < 0 else "") + s


def reference(shapes):
    A = [b * h for b, h, _, _ in shapes]
    tot = sum(A)
    xc = sum(x * a for (_, _, x, _), a in zip(shapes, A)) / tot
    yc = sum(y * a for (_, _, _, y), a in zip(shapes, A)) / tot
    rows = []
    for (b, h, x, y), a in zip(shapes, A):
        dx, dy = x - xc, y - yc            # shape − centroid
        rows.append([a, b * h ** 3 / 12, b ** 3 * h / 12, dx, dy,
                     dy * dy * a, dx * dx * a, -dx * dy * a])
    ix = sum(r[1] + r[5] for r in rows)
    iy = sum(r[2] + r[6] for r in rows)
    ixy = sum(r[7] for r in rows)
    io = (ix + iy) / 2
    r = math.hypot((ix - iy) / 2, ixy)
    beta = math.degrees(math.atan2(2 * ixy, ix - iy)) / 2
    return rows, [tot, xc, yc, ix, iy, ixy], [io, r, io + r, io - r, beta]


def start(calc, choice, inputs=(), settle=4.0):
    """Launch AREAMOM, pick menu item 1 (MATRIX), 2 (TYPE CENTROIDS) or 3 (TYPE VERTICES), answer prompts."""
    calc.run_program("AREAMOM", settle=0.5)
    calc.press("K%d" % choice)
    calc.run(1.5)
    for s in inputs:
        calc.type(s)
        calc.press("ENTER")
        calc.run(1.5)
    calc.run(settle)
    return calc.text()


def typed(calc, inputs, settle=4.0):
    return start(calc, 2, inputs, settle)


def corners(shape, flip=False):
    """Two opposite corners (x1, y1, x2, y2) of the rectangle whose centroid is shape's."""
    b, h, x, y = shape
    dx, dy = abs(b) / 2, abs(h) / 2
    return (x - dx, y + dy, x + dx, y - dy) if flip else (x - dx, y - dy, x + dx, y + dy)


def vertex_rows(shapes, flip=False):
    return [list(s[:2]) + list(corners(s, flip)) for s in shapes]


def pages(calc, first, n_shapes, settle=4.0):
    """`first` plus every later page (ENTER between them)."""
    screens = [first]
    assert calc.error() is None, first
    for _ in range(n_shapes + 1):
        calc.press("ENTER")
        calc.run(settle)
        screens.append(calc.text())
        assert calc.error() is None, screens[-1]
    return screens


def run(calc, shapes, settle=4.0):
    """Type the shapes in by hand, then page through every screen."""
    ins = [str(len(shapes))] + [num(v) for s in shapes for v in s]
    return pages(calc, typed(calc, ins, settle), len(shapes), settle)


def run_vertices(calc, shapes, settle=4.0, flip=False):
    """Type the shapes in as B, H, x1, y1, x2, y2 (menu item 3)."""
    ins = [str(len(shapes))] + [num(v) for r in vertex_rows(shapes, flip) for v in r]
    return pages(calc, start(calc, 3, ins, settle), len(shapes), settle)


def put(calc, letter, rows):
    calc.send_var(T_MATRIX, bytes([0x5C, "ABCDEFGHIJ".index(letter)]), matrix_data(rows))


def run_matrix(calc, letter, shapes, settle=4.0, vertices=False, flip=False):
    """Store the shapes as matrix [letter] (rows = shapes; cols = b h x y, or
    b h x1 y1 x2 y2 with vertices=True), use MATRIX."""
    put(calc, letter, vertex_rows(shapes, flip) if vertices else [list(s) for s in shapes])
    return pages(calc, start(calc, 1, [letter], settle), len(shapes), settle)


def value(line, label, end=16):
    """Parse the right-aligned number after `label`; checks it didn't wrap."""
    assert line.startswith(label), (label, line)
    raw = line[:end].rstrip("?")  # β's trailing ° reads as ?
    assert len(raw) == end, ("not right-aligned to col %d" % end, line)
    txt = raw[len(label):].strip()
    assert txt and " " not in txt, (label, line)
    return txt


def to_float(txt):
    return float(txt.replace("⁻", "-").replace("ᴇ", "e"))


def shown_close(txt, want):
    """`txt` is `want` correctly rounded to the digits it shows (≥3 sig figs)."""
    got = to_float(txt)
    if want == 0 or abs(want) < 1e-12:
        assert got == 0, (txt, want)
        return
    mant = re.sub(r"ᴇ.*", "", txt).replace("⁻", "").replace(".", "").lstrip("0")
    if "." in txt or "ᴇ" in txt:
        digits = len(mant)
    else:  # integer: trailing zeros may be rounding (the program shows ≤6 sig figs)
        digits = max(len(mant.rstrip("0")), min(len(mant), 6))
    exp = math.floor(math.log10(abs(got)))
    ulp = 10 ** (exp - digits + 1)
    assert abs(got - want) <= 0.5 * ulp * 1.0001 + 1e-12 * abs(want), (txt, want)
    assert len(mant) >= 3 or abs(got - want) <= 1e-9 * abs(want), ("too few digits", txt, want)


def check_all(screens, shapes):
    rows, totals, princ = reference(shapes)
    n = len(shapes)
    for k in range(n):
        s = screens[k]
        assert s[0].startswith("#%d" % (k + 1)), s
        head = s[0][s[0].index("A="):]
        shown_close(value(head, "A=", end=15 - s[0].index("A=")), rows[k][0])
        for line, label, want in zip(s[1:], SHAPE_LABELS[1:], rows[k][1:]):
            shown_close(value(line, label), want)
    s = screens[n]
    assert s[0] == "TOTAL (IN [I])" and s[1] == "", s
    for line, label, want in zip(s[2:], TOTAL_LABELS, totals):
        shown_close(value(line, label), want)
    s = screens[n + 1]
    assert s[0] == "PRINCIPAL" and s[1] in ("", "█"), s  # cursor blinks here
    for line, label, want in zip(s[2:6], PRINC_LABELS, princ):
        shown_close(value(line, label), want)
    if princ[1] > 1e-9 * princ[0]:
        shown_close(value(s[6], "?=", end=15), princ[4])
        assert s[6].endswith("?"), s  # the ° sign
    return rows, totals, princ


# --- MECH 360 worked examples -------------------------------------------------

def test_L_channel_matches_lecture_notes(calc):
    screens = run(calc, L_CHANNEL)
    check_all(screens, L_CHANNEL)
    # L6 §3.2 table and Mohr results, digit for digit as printed in the notes
    assert screens[0][5].endswith("144970") and screens[0][6].endswith("106509"), screens[0]
    assert screens[0][7].endswith("124260"), screens[0]
    assert screens[1][5].endswith("231953") and screens[1][7].endswith("198817"), screens[1]
    t = screens[2]
    assert t[3].endswith("11.5385") and t[4].endswith("21.5385"), t
    assert [to_float(value(l, lb)) for l, lb in zip(t[5:], TOTAL_LABELS[3:])] == \
        [807756, 387756, 323077], t  # 8.0776, 3.8776, 3.2308 ×10⁵
    p = screens[3]
    assert [to_float(value(l, lb)) for l, lb in zip(p[2:6], PRINC_LABELS)] == \
        [597756, 385329, 983086, 212427], p  # 5.9776 3.8533 9.8309 2.1243 ×10⁵
    assert "28.4881" in p[6], p  # β = 28.49°


def test_Z_section_matches_lecture_notes(calc):
    screens = run(calc, Z_SECTION)
    check_all(screens, Z_SECTION)
    t = screens[3]
    assert t[3].endswith("0") and t[4].endswith("0"), t  # centroid at origin
    assert [to_float(value(l, lb)) for l, lb in zip(t[5:], TOTAL_LABELS[3:])] == \
        [614167, 1894170, 800000], t  # 6.142e5, 1.8942e6, 8e5
    assert screens[0][7].endswith("400000") and screens[1][7].endswith(" 0"), screens


def test_tensor_stored_in_matrix_I_full_precision(calc):
    run(calc, L_CHANNEL)
    _, (tot, xc, yc, ix, iy, ixy), _ = reference(L_CHANNEL)
    m = decode_matrix(calc.recv_var(T_MATRIX, MAT_I))
    want = [[ix, ixy], [ixy, iy]]
    for gr, wr in zip(m, want):
        for g, w in zip(gr, wr):
            assert abs(g - w) <= 1e-9 * abs(w), (m, want)


def test_results_list_MOA(calc):
    run(calc, L_CHANNEL)
    got = decode_list(calc.recv_var(T_LIST, b"\x5dMOA"))
    _, totals, princ = reference(L_CHANNEL)
    want = totals + princ
    assert len(got) == 11, got
    for g, w in zip(got, want):
        assert abs(g - w) <= 1e-9 * max(1, abs(w)), (got, want)


def test_per_shape_columns_kept_for_stat_editor(calc):
    run(calc, L_CHANNEL)
    rows, _, _ = reference(L_CHANNEL)
    for name, col in [(b"MA", 0), (b"MIX", 1), (b"MIY", 2), (b"MDX", 3), (b"MDY", 4),
                      (b"MTX", 5), (b"MTY", 6), (b"MTXY", 7)]:
        got = decode_list(calc.recv_var(T_LIST, b"\x5d" + name))
        for g, r in zip(got, rows):
            assert abs(g - r[col]) <= 1e-9 * max(1, abs(r[col])), (name, got)


def test_delta_is_shape_minus_centroid(calc):
    screens = run(calc, L_CHANNEL)
    # shape 1 is left of and above the centroid
    assert value(screens[0][3], "?x?*=") == "⁻11.5385", screens[0]
    assert value(screens[0][4], "?y?*=") == "13.4615", screens[0]


# --- principal axes -----------------------------------------------------------

def test_beta_points_at_strong_axis(calc):
    for shapes in (L_CHANNEL, Z_SECTION, [(10, 80, 0, 35), (50, 10, -30, 0)]):
        _, (_, _, _, ix, iy, ixy), (io, r, istr, iwk, beta) = reference(shapes)
        c, s = math.cos(math.radians(beta)), math.sin(math.radians(beta))
        assert abs(c * c * ix + 2 * s * c * ixy + s * s * iy - istr) < 1e-6 * istr
    screens = run(calc, Z_SECTION)
    _, _, princ = reference(Z_SECTION)
    shown_close(value(screens[4][6], "?=", end=15), princ[4])  # 64.33°: past 45°


def test_radian_mode_still_gives_degrees(calc):
    from tibasic import compile_source
    import os, tempfile
    p = compile_source("Radian", "SETRAD")
    path = os.path.join(tempfile.mkdtemp(), "SETRAD.8xp")
    p.save(path)
    calc.send_file(path)
    calc.run_program("SETRAD")
    screens = run(calc, L_CHANNEL)
    assert "28.4881" in screens[3][6], screens[3]


def test_symmetric_I_beam_has_zero_product(calc):
    beam = [(100, 10, 0, 55), (10, 100, 0, 0), (100, 10, 0, -55)]
    screens = run(calc, beam)
    check_all(screens, beam)
    t, p = screens[3], screens[4]
    assert value(t[7], "I_xy=") == "0", t
    assert value(p[6], "?=", end=15) == "0", p  # Ix > Iy: strong axis is x


def test_tall_section_beta_is_90(calc):
    flat = [(100, 10, 0, 0), (60, 10, 0, 10)]  # wide and flat: weak about x
    _, (_, _, _, ix, iy, _), _ = reference(flat)
    assert iy > ix
    screens = run(calc, flat)
    assert value(screens[3][6], "?=", end=15) == "90", screens[3]


def test_square_any_axis(calc):
    screens = run(calc, [(20, 20, 5, 5)])
    p = screens[2]
    assert value(p[3], "R=") == "0", p
    assert p[6].replace(" ", "") == "?=ANYAXIS", p


# --- holes, units, number formatting ----------------------------------------

def test_hole_as_negative_b(calc):
    plate = [(100, 100, 0, 0), (-20, 40, 20, 10)]
    screens = run(calc, plate)
    rows, totals, _ = check_all(screens, plate)
    assert totals[0] == 9200
    assert value(screens[1][0][screens[1][0].index("A="):], "A=", end=15 - screens[1][0].index("A=")) == "⁻800"


def test_metres_small_values_fit(calc):
    # mirrored L in metres: negative products, ᴇ-notation everywhere
    shapes = [(0.01, 0.08, 0, 0.035), (0.05, 0.01, -0.03, 0)]
    screens = run(calc, shapes)
    check_all(screens, shapes)
    assert "ᴇ" in screens[0][7] and "⁻" in screens[0][7], screens[0]


def test_large_values_fit(calc):
    shapes = [(2500, 40000, 123456, -98765.4321), (30000, 1500, -4321, 20000)]
    screens = run(calc, shapes)
    check_all(screens, shapes)
    assert any("ᴇ" in l for l in screens[2]), screens[2]


def test_random_sections_never_wrap(calc):
    rnd = random.Random(360)
    for _ in range(3):
        calc.press("CLEAR")
        scale = 10 ** rnd.randint(-3, 3)
        shapes = [(round(rnd.uniform(1, 90) * scale, 6) * rnd.choice([1, 1, 1, -1]) or scale,
                   round(rnd.uniform(1, 90) * scale, 6),
                   round(rnd.uniform(-90, 90) * scale, 6),
                   round(rnd.uniform(-90, 90) * scale, 6)) for _ in range(rnd.randint(1, 4))]
        shapes[0] = (abs(shapes[0][0]) * 50, shapes[0][1] * 3) + shapes[0][2:]  # area > 0
        check_all(run(calc, shapes), shapes)


# --- input handling and variable safety --------------------------------------

def test_zero_and_fractional_shape_counts_rejected(calc):
    for bad in ["0", "1.5"]:
        calc.press("CLEAR")
        screen = typed(calc, [bad])
        assert "NEED 1-99 SHAPES" in screen, screen


def test_hole_as_negative_h(calc):
    plate = [(100, 100, 0, 0), (20, -40, 20, 10)]
    screens = run(calc, plate)
    check_all(screens, plate)
    # same physical hole as a negative b gives identical totals
    calc.press("CLEAR")
    other = run(calc, [(100, 100, 0, 0), (-20, 40, 20, 10)])
    assert other[2] == screens[2] and other[3] == screens[3], (other, screens)


def test_b_and_h_both_negative_reprompts(calc):
    ins = ["2", "100", "100", "0", "0", "~10", "~20"]
    screen = typed(calc, ins, settle=3)
    assert "ONLY B OR H <0" in screen, screen
    calc.type("20\n0\n0\n")   # H again, X₀*, Y₀*
    calc.run(4)
    calc.press("ENTER")          # past shape 1's page
    calc.run(4)
    s = calc.text()
    assert calc.error() is None, s
    assert s[0].startswith("#2") and s[0].endswith("⁻200"), s  # still a hole


def test_b_zero_and_h_zero_reprompt(calc):
    screen = typed(calc, ["1", "0", "10", "0", "20"], settle=3)
    assert "B MUST NOT BE 0" in screen and "H MUST NOT BE 0" in screen, screen
    calc.type("0\n0\n")   # X₀*, Y₀*
    calc.run(4)
    assert calc.text()[0].startswith("#1"), calc.text()
    assert calc.text()[1].endswith("6666.67"), calc.text()  # 10·20³/12


def test_expressions_accepted(calc):
    ins = ["2", "20/2", "8*10", "0", "70/2", "50", "10", "15+15", "0"]
    screen = typed(calc, ins)
    assert screen[0].replace(" ", "") == "#1A=800", screen


def test_total_area_not_positive(calc):
    screen = typed(calc, ["2", "10", "10", "0", "0", "~20", "10", "0", "0"])
    assert "TOTAL AREA ?0" in screen or "TOTAL AREA ≤0" in screen, screen


def test_other_vars_untouched_and_temps_cleaned(calc):
    calc.send_var(T_MATRIX, b"\x5c\x00", matrix_data([[1, 2], [3, 4]]))
    for v, x in [(b"A", 3), (b"B", 4), (b"I", 5), (b"K", 6), (b"R", 7), (b"X", 8), (b"Y", 9)]:
        calc.send_var(T_REAL, v, tifloat_encode(x))
    run(calc, L_CHANNEL)
    assert decode_matrix(calc.recv_var(T_MATRIX, b"\x5c\x00")) == [[1, 2], [3, 4]]
    for v, x in [(b"A", 3), (b"B", 4), (b"I", 5), (b"K", 6), (b"R", 7), (b"X", 8), (b"Y", 9)]:
        assert decode_real(calc.recv_var(T_REAL, v)) == x, v
    for tmp in [b"MV", b"MW", b"ME", b"MM", b"MS", b"MT", b"MQ", b"MN", b"MZ", b"MK"]:
        try:
            calc.recv_var(T_LIST, b"\x5d" + tmp)
        except Exception:
            continue
        raise AssertionError("temp list %r left behind" % tmp)


# --- matrix input -------------------------------------------------------------

def test_menu_offers_matrix_and_typing(calc):
    screen = calc.run_program("AREAMOM", settle=0.5)
    assert screen[0].strip() == "AREA MOMENTS", screen
    assert "1:MATRIX" in screen[1] and "2:TYPE CENTROIDS" in screen[2], screen
    assert "3:TYPE VERTICES" in screen[3], screen


def test_matrix_screen_explains_format(calc):
    screen = start(calc, 1, settle=0.5)
    assert screen[0] == "ROWS: SHAPES", screen
    assert screen[1] == "COL:B H X?* Y?*", screen
    assert screen[2] == "OR:B H X1Y1X2Y2", screen
    assert screen[3].startswith("MATRIX A-J?"), screen


def test_matrix_L_channel_same_as_typed(calc):
    by_matrix = run_matrix(calc, "C", L_CHANNEL)
    check_all(by_matrix, L_CHANNEL)
    calc.press("CLEAR")
    assert run(calc, L_CHANNEL) == by_matrix


def test_matrix_Z_section_in_J(calc):
    check_all(run_matrix(calc, "J", Z_SECTION), Z_SECTION)


def test_matrix_single_row_and_holes(calc):
    check_all(run_matrix(calc, "A", [(20, 20, 5, 5)]), [(20, 20, 5, 5)])
    calc.press("CLEAR")
    plate = [(100, 100, 0, 0), (-20, 40, 20, 10), (10, -10, -30, -30)]
    check_all(run_matrix(calc, "B", plate), plate)


def test_matrix_left_untouched_and_tensor_in_I(calc):
    rows = [list(s) for s in Z_SECTION]
    run_matrix(calc, "D", Z_SECTION)
    assert decode_matrix(calc.recv_var(T_MATRIX, b"\x5c\x03")) == rows
    _, (_, _, _, ix, iy, ixy), _ = reference(Z_SECTION)
    m = decode_matrix(calc.recv_var(T_MATRIX, MAT_I))
    assert all(abs(g - w) <= 1e-9 * abs(w) for g, w in zip(m[0] + m[1], [ix, ixy, ixy, iy])), m


def test_matrix_bad_name(calc):
    for bad in ["K", "AB"]:
        calc.press("CLEAR")
        screen = start(calc, 1, [bad])
        assert "NAME MUST BE A-J" in screen, screen


def test_matrix_wrong_column_count(calc):
    put(calc, "E", [[10, 80, 0], [50, 10, 30]])
    screen = start(calc, 1, ["E"])
    assert "4 OR 6 COLUMNS:" in screen, screen


def test_matrix_zero_dimension_names_row(calc):
    put(calc, "F", [[10, 80, 0, 35], [50, 0, 30, 0], [5, 5, 0, 0]])
    screen = start(calc, 1, ["F"])
    i = screen.index("BAD SHAPE/ROW:")
    assert screen[i + 1].strip() == "2" and "B OR H IS 0" in screen, screen


def test_matrix_both_negative_names_row(calc):
    put(calc, "G", [[10, 80, 0, 35], [50, 10, 30, 0], [-5, -5, 0, 0]])
    screen = start(calc, 1, ["G"])
    i = screen.index("BAD SHAPE/ROW:")
    assert screen[i + 1].strip() == "3" and "B AND H BOTH <0" in screen, screen


def test_matrix_undefined(calc):
    start(calc, 1, ["H"])
    assert calc.error() == "UNDEFINED"


# --- vertex entry: B, H, x1, y1, x2, y2 ---------------------------------------

def test_vertices_typed_match_centroids_L_channel(calc):
    cent = run(calc, L_CHANNEL)
    calc.press("CLEAR")
    vert = run_vertices(calc, L_CHANNEL)
    check_all(vert, L_CHANNEL)
    assert vert == cent, (vert, cent)


def test_vertices_typed_other_diagonal_and_holes(calc):
    plate = [(100, 100, 0, 0), (-20, 40, 20, 10)]
    check_all(run_vertices(calc, plate, flip=True), plate)
    calc.press("CLEAR")
    plate_h = [(100, 100, 0, 0), (20, -40, 20, 10)]
    check_all(run_vertices(calc, plate_h), plate_h)


def test_vertices_typed_Z_section_and_small_values(calc):
    check_all(run_vertices(calc, Z_SECTION), Z_SECTION)
    calc.press("CLEAR")
    metres = [(0.01, 0.08, 0, 0.035), (0.05, 0.01, -0.03, 0)]
    check_all(run_vertices(calc, metres), metres)


def test_vertex_prompts_in_order_with_expressions(calc):
    screen = start(calc, 3, ["1", "10", "20", "~5+0"], settle=1)
    assert any(l.startswith("Y1=") for l in screen), screen
    calc.type("0\n5*1\n20/1\n")
    calc.run(4)
    s = calc.text()
    assert calc.error() is None, s
    assert s[0].replace(" ", "") == "#1A=200", s
    calc.press("ENTER")
    calc.run(4)
    t = calc.text()
    assert value(t[3], "x?*=") == "0", t     # (-5 + 5) / 2
    assert value(t[4], "y?*=") == "10", t    # (0 + 20) / 2


def test_matrix_vertices_same_as_typed_centroids(calc):
    by_matrix = run_matrix(calc, "C", L_CHANNEL, vertices=True)
    check_all(by_matrix, L_CHANNEL)
    calc.press("CLEAR")
    assert run(calc, L_CHANNEL) == by_matrix


def test_matrix_vertices_Z_section_holes_flipped(calc):
    check_all(run_matrix(calc, "J", Z_SECTION, vertices=True, flip=True), Z_SECTION)
    calc.press("CLEAR")
    plate = [(100, 100, 0, 0), (-20, 40, 20, 10), (10, -10, -30, -30)]
    check_all(run_matrix(calc, "B", plate, vertices=True), plate)


def test_matrix_vertices_left_untouched(calc):
    rows = vertex_rows(Z_SECTION)
    run_matrix(calc, "D", Z_SECTION, vertices=True)
    assert decode_matrix(calc.recv_var(T_MATRIX, b"\x5c\x03")) == rows


def test_matrix_vertices_bad_row_still_named(calc):
    put(calc, "G", [[10, 80, 0, 0, 10, 80], [50, 0, 30, 0, 80, 0], [5, 5, 0, 0, 5, 5]])
    screen = start(calc, 1, ["G"])
    i = screen.index("BAD SHAPE/ROW:")
    assert screen[i + 1].strip() == "2" and "B OR H IS 0" in screen, screen


def test_matrix_five_columns_rejected(calc):
    put(calc, "E", [[10, 80, 0, 0, 10], [50, 10, 30, 0, 80]])
    assert "4 OR 6 COLUMNS:" in start(calc, 1, ["E"])


def test_vertex_mode_cleans_temp_lists(calc):
    run_vertices(calc, L_CHANNEL)
    calc.press("CLEAR")
    run_matrix(calc, "A", L_CHANNEL, vertices=True)
    for tmp in [b"MV", b"MW", b"MK", b"MT"]:
        try:
            calc.recv_var(T_LIST, b"\x5d" + tmp)
        except Exception:
            continue
        raise AssertionError("temp list %r left behind" % tmp)


# --- vertex mode: B/H must match the corners ------------------------------------

def test_typed_vertices_x_mismatch_names_shape_and_axis(calc):
    # shape 2: B=50 but corners are 60 apart in x (y is fine)
    ins = ["2", "10", "80", "~5", "~5", "5", "75", "50", "10", "5", "~5", "65", "5"]
    s = start(calc, 3, ins, settle=2)
    assert s[0].replace(" ", "") == "SHAPE2ERROR", s
    assert s[1] == "X: B≠|X2-X1|", s
    assert s[2].replace(" ", "") == "B=50" and s[3].replace(" ", "") == "|X2-X1|=60", s
    assert not any(l.startswith("Y:") for l in s), s
    assert s[7] == "ENTER: RETYPE", s


def test_typed_vertices_y_mismatch(calc):
    s = start(calc, 3, ["1", "10", "20", "0", "0", "10", "25"], settle=2)
    assert s[0].replace(" ", "") == "SHAPE1ERROR" and s[4] == "Y: H≠|Y2-Y1|", s
    assert not any(l.startswith("X:") for l in s), s
    assert s[5].replace(" ", "") == "H=20" and s[6].replace(" ", "") == "|Y2-Y1|=25", s


def test_typed_vertices_both_axes_mismatch(calc):
    s = start(calc, 3, ["1", "10", "20", "0", "0", "11", "21"], settle=2)
    assert s[1].startswith("X:") and s[4].startswith("Y:"), s


def test_typed_vertices_retype_after_error(calc):
    ins = ["1", "10", "20", "0", "0", "12", "20"]
    s = start(calc, 3, ins, settle=2)
    assert s[1].startswith("X:"), s
    calc.press("ENTER")        # retype the whole shape
    calc.run(1.5)
    assert any(l.startswith("B=") for l in calc.text()), calc.text()
    for v in ["10", "20", "0", "0", "10", "20"]:
        calc.type(v + "\n")
        calc.run(1.5)
    calc.run(4)
    t = calc.text()
    assert calc.error() is None and t[0].replace(" ", "") == "#1A=200", t


def test_typed_vertices_holes_compare_magnitudes(calc):
    plate = [(100, 100, 0, 0), (-20, 40, 20, 10)]
    check_all(run_vertices(calc, plate), plate)        # B=-20 vs corners 20 apart: OK


def test_matrix_vertices_mismatch_names_row_and_axis(calc):
    rows = [[10, 80, -5, -5, 5, 75], [50, 10, 5, -5, 55, 5], [5, 5, 0, 0, 5, 6]]
    put(calc, "F", rows)
    s = start(calc, 1, ["F"])
    i = s.index("BAD SHAPE/ROW:")
    assert s[i + 1].strip() == "3" and "Y: H≠|Y2-Y1|" in s and not any(l.startswith("X:") for l in s), s
    calc.press("CLEAR")
    rows[2] = [5, 5, 0, 0, 6, 6]
    put(calc, "F", rows)
    s = start(calc, 1, ["F"])
    assert s[s.index("BAD SHAPE/ROW:") + 1].strip() == "3" and "X: B≠|X2-X1|" in s and "Y: H≠|Y2-Y1|" in s, s
    calc.press("CLEAR")
    rows[2] = [5, 5, 0, 0, 5, 5]
    rows[0] = [10, 80, -5, -5, 6, 75]
    put(calc, "F", rows)
    s = start(calc, 1, ["F"])
    assert s[s.index("BAD SHAPE/ROW:") + 1].strip() == "1" and "X: B≠|X2-X1|" in s, s
