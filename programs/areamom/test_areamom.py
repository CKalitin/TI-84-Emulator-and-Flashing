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


def run(calc, shapes, settle=4.0):
    """Enter the shapes, then page through every screen. Returns the list of screens."""
    ins = [str(len(shapes))] + [num(v) for s in shapes for v in s]
    screens = [calc.run_program("AREAMOM", inputs=ins, settle=settle)]
    assert calc.error() is None, screens[-1]
    for _ in range(len(shapes) + 1):
        calc.press("ENTER")
        calc.run(settle)
        screens.append(calc.text())
        assert calc.error() is None, screens[-1]
    return screens


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
    assert s[0] == "PRINCIPAL" and s[1] == "", s
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
        screen = calc.run_program("AREAMOM", inputs=[bad])
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
    screen = calc.run_program("AREAMOM", inputs=ins, settle=3)
    assert "ONLY B OR H <0" in screen, screen
    calc.type("20\n0\n0\n")   # H again, X₀*, Y₀*
    calc.run(4)
    calc.press("ENTER")          # past shape 1's page
    calc.run(4)
    s = calc.text()
    assert calc.error() is None, s
    assert s[0].startswith("#2") and s[0].endswith("⁻200"), s  # still a hole


def test_b_zero_and_h_zero_reprompt(calc):
    screen = calc.run_program("AREAMOM", inputs=["1", "0", "10", "0", "20"], settle=3)
    assert "B MUST NOT BE 0" in screen and "H MUST NOT BE 0" in screen, screen
    calc.type("0\n0\n")   # X₀*, Y₀*
    calc.run(4)
    assert calc.text()[0].startswith("#1"), calc.text()
    assert calc.text()[1].endswith("6666.67"), calc.text()  # 10·20³/12


def test_expressions_accepted(calc):
    ins = ["2", "20/2", "8*10", "0", "70/2", "50", "10", "15+15", "0"]
    screen = calc.run_program("AREAMOM", inputs=ins, settle=4)
    assert screen[0].replace(" ", "") == "#1A=800", screen


def test_total_area_not_positive(calc):
    screen = calc.run_program("AREAMOM", inputs=["2", "10", "10", "0", "0", "~20", "10", "0", "0"])
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
