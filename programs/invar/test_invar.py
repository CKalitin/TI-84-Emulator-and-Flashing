"""Emulator tests for INVAR.  Run: ./ti84 test programs/invar

INVAR takes a stress tensor stored in a matrix [A]..[J] (3×3, or 2×2 for plane
stress) and shows I1, I2, I3, J2, J3 right-aligned like AREAMOM. Expected values
come from `reference()`, which uses the MECH 360 cheat-sheet forms
(J2 = I1²/3 − I2, J3 = 2I1³/27 − I1·I2/3 + I3) rather than the deviatoric forms
the program uses, so the two are independent.
"""
import math
import random
import re

from ti84emu import (decode_list, decode_matrix, decode_real, matrix_data, tifloat_encode,
                     T_LIST, T_MATRIX, T_REAL)

MAT = {c: bytes([0x5C, i]) for i, c in enumerate("ABCDEFGHIJ")}
LABELS = ["I_1=", "I_2=", "I_3=", "J_2=", "J_3="]
TEMPS = [b"IVT", b"IVX", b"IVY", b"IVZ", b"IVS", b"IVG", b"IVQ", b"IVR", b"IVN", b"IVF"]
GENERAL = [[50, 30, 20], [30, -20, -10], [20, -10, 10]]


def reference(rows):
    if len(rows) == 2:
        rows = [rows[0] + [0], rows[1] + [0], [0, 0, 0]]
    (sx, txy, txz), (_, sy, tyz), (_, _, sz) = rows
    i1 = sx + sy + sz
    i2 = sx * sy + sy * sz + sz * sx - txy ** 2 - tyz ** 2 - txz ** 2
    i3 = sx * sy * sz + 2 * txy * tyz * txz - sx * tyz ** 2 - sy * txz ** 2 - sz * txy ** 2
    return [i1, i2, i3, i1 ** 2 / 3 - i2, 2 / 27 * i1 ** 3 - i1 * i2 / 3 + i3]


def put(calc, name, rows):
    calc.send_var(T_MATRIX, MAT[name], matrix_data(rows))


def start(calc, name, settle=5.0):
    return calc.run_program("INVAR", inputs=[name], settle=settle)


def run(calc, name, rows):
    put(calc, name, rows)
    screen = start(calc, name)
    assert calc.error() is None, screen
    assert screen[0] == "INVARIANTS [%s]" % name, screen
    assert re.fullmatch(r"\(IN .IVAR\)", screen[1]), screen  # ʟ may not OCR
    return screen


def value(line, label):
    """The number after `label`, right-aligned to column 16 with no wrap."""
    assert line.startswith(label), (label, line)
    assert len(line) == 16, ("not right-aligned to col 16", line)
    txt = line[len(label):].strip()
    assert txt and " " not in txt, (label, line)
    return txt


def to_float(txt):
    return float(txt.replace("⁻", "-").replace("ᴇ", "e"))


def shown_close(txt, want, scale):
    """`txt` is `want` rounded to the digits shown; ~0 relative to `scale` shows as 0."""
    got = to_float(txt)
    if abs(want) < 1e-10 * scale:
        assert got == 0, (txt, want)
        return
    mant = re.sub(r"ᴇ.*", "", txt).replace("⁻", "").replace(".", "").lstrip("0")
    if "." in txt or "ᴇ" in txt:
        digits = len(mant)
    else:  # integer: trailing zeros may be rounding (≤6 sig figs shown)
        digits = max(len(mant.rstrip("0")), min(len(mant), 6))
    ulp = 10 ** (math.floor(math.log10(abs(got))) - digits + 1)
    assert abs(got - want) <= 0.5 * ulp * 1.0001 + 1e-9 * abs(want), (txt, want)
    assert len(mant) >= 3 or abs(got - want) <= 1e-9 * abs(want), ("too few digits", txt, want)


def check(screen, rows):
    s = max(abs(v) for r in rows for v in r)
    shown = [value(line, label) for line, label in zip(screen[2:7], LABELS)]
    for txt, want, p in zip(shown, reference(rows), [1, 2, 3, 2, 3]):
        shown_close(txt, want, s ** p)
    return shown


def recv_list(calc, name):
    return decode_list(calc.recv_var(T_LIST, b"\x5d" + name))


def missing(calc, typ, name):
    try:
        calc.recv_var(typ, name)
    except Exception:
        return True
    return False


# --- results ------------------------------------------------------------------

def test_general_3x3(calc):
    shown = check(run(calc, "A", GENERAL), GENERAL)
    assert shown == ["40", "⁻2100", "⁻28000", "2633.33", "4740.74"], shown


def test_results_list_IVAR_full_precision(calc):
    run(calc, "A", GENERAL)
    got = recv_list(calc, b"IVAR")
    want = reference(GENERAL)
    assert len(got) == 5, got
    for g, w in zip(got, want):
        assert abs(g - w) <= 1e-9 * abs(w), (got, want)


def test_plane_stress_2x2(calc):
    m = [[80, -25], [-25, 40]]
    shown = check(run(calc, "B", m), m)
    assert shown[2] == "0", shown  # σz = 0 → I3 = 0


def test_2x2_matches_padded_3x3(calc):
    a = run(calc, "C", [[12.5, 4], [4, -7]])
    calc.press("CLEAR")
    b = run(calc, "D", [[12.5, 4, 0], [4, -7, 0], [0, 0, 0]])
    assert a[2:7] == b[2:7], (a, b)


def test_uniaxial(calc):
    m = [[100, 0, 0], [0, 0, 0], [0, 0, 0]]
    shown = check(run(calc, "E", m), m)
    assert shown == ["100", "0", "0", "3333.33", "74074.1"], shown


def test_pure_shear(calc):
    m = [[0, 50, 0], [50, 0, 0], [0, 0, 0]]
    shown = check(run(calc, "F", m), m)
    assert shown == ["0", "⁻2500", "0", "2500", "0"], shown


def test_hydrostatic_has_no_deviatoric_part(calc):
    m = [[-30, 0, 0], [0, -30, 0], [0, 0, -30]]
    shown = check(run(calc, "G", m), m)
    assert shown == ["⁻90", "2700", "⁻27000", "0", "0"], shown


def test_non_terminating_hydrostatic_J_exactly_zero(calc):
    m = [[1 / 3, 0, 0], [0, 1 / 3, 0], [0, 0, 1 / 3]]  # I1/3 rounds; J2, J3 must still be 0
    shown = check(run(calc, "H", m), m)
    assert shown[3:] == ["0", "0"], shown


def test_zero_tensor(calc):
    m = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    assert check(run(calc, "I", m), m) == ["0"] * 5


def test_decimals_and_negatives(calc):
    m = [[-12.75, 3.5, -0.25], [3.5, 8.125, 6.5], [-0.25, 6.5, -4.4]]
    check(run(calc, "J", m), m)


def test_pascals_large_values_fit(calc):
    m = [[250e6, -80e6, 35e6], [-80e6, -120e6, 60e6], [35e6, 60e6, 75e6]]
    shown = check(run(calc, "A", m), m)
    assert all("ᴇ" in t for t in shown[1:]), shown


def test_tiny_values_fit(calc):
    m = [[2.5e-4, -1e-4, 0], [-1e-4, -3e-4, 7e-5], [0, 7e-5, 1.2e-4]]
    shown = check(run(calc, "A", m), m)
    assert all("ᴇ" in t for t in shown[1:]), shown


def test_random_tensors_never_wrap(calc):
    rnd = random.Random(360)
    for _ in range(6):
        calc.press("CLEAR")
        k = rnd.choice([2, 3])
        scale = 10 ** rnd.randint(-5, 7)
        m = [[round(rnd.uniform(-99, 99), rnd.randint(0, 3)) * scale for _ in range(k)]
             for _ in range(k)]
        for i in range(k):
            for j in range(i):
                m[i][j] = m[j][i]
        check(run(calc, "A", m), m)


def test_works_from_every_matrix_name(calc):
    for c in "ABCDEFGHIJ":
        calc.press("CLEAR")
        m = [[1, 2, 3], [2, 4, 5], [3, 5, "ABCDEFGHIJ".index(c)]]
        check(run(calc, c, m), m)


def test_tolerates_rounding_level_asymmetry(calc):
    m = [[100, 1 / 3, 0], [0.333333333333, -50, 0], [0, 0, 20]]  # e.g. a computed tensor
    check(run(calc, "A", m), [[100, 1 / 3, 0], [1 / 3, -50, 0], [0, 0, 20]])


# --- input checking -----------------------------------------------------------

def test_header_explains_input(calc):
    screen = calc.run_program("INVAR", settle=0.5)
    assert screen[0] == "INVARIANTS", screen
    assert screen[1][1:] == ": 3X3 OR 2X2", screen  # σ doesn't OCR
    assert screen[2] == "SYMMETRIC", screen
    assert screen[3].startswith("MATRIX A-J?"), screen


def test_no_typing_mode(calc):
    """Only a matrix name is asked for: no menu, no element prompts."""
    put(calc, "A", GENERAL)
    calc.run_program("INVAR", settle=0.5)
    calc.type("A")
    calc.press("ENTER")
    calc.run(5)
    s = calc.text()
    assert s[0] == "INVARIANTS [A]", s


def test_bad_name(calc):
    for bad in ["K", "AB", "1"]:
        calc.press("CLEAR")
        screen = start(calc, bad)
        assert calc.error() is None, screen
        assert "NAME MUST BE A-J" in screen, screen


def test_not_square(calc):
    put(calc, "A", [[1, 2, 3], [4, 5, 6]])
    screen = start(calc, "A")
    assert calc.error() is None, screen
    i = screen.index("NEED 3X3 OR 2X2")
    assert screen[i + 1] == "GOT", screen
    assert screen[i + 2].replace(" ", "") == "{23}", screen


def test_wrong_size(calc):
    for rows in ([[5]], [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]):
        calc.press("CLEAR")
        put(calc, "B", rows)
        screen = start(calc, "B")
        assert calc.error() is None, screen
        assert "NEED 3X3 OR 2X2" in screen, screen


def test_not_symmetric_names_each_pair(calc):
    put(calc, "C", [[1, 2, 3], [9, 5, 6], [3, 7, 9]])
    screen = start(calc, "C")
    assert calc.error() is None, screen
    i = screen.index("NOT SYMMETRIC:")
    pairs = [re.sub(r"\)[^(]\(", ")≠(", l) for l in screen[i + 1:]]  # ≠ may OCR as ?
    assert pairs[:2] == ["(1,2)≠(2,1)", "(2,3)≠(3,2)"], screen
    assert "(1,3)≠(3,1)" not in pairs, screen


def test_not_symmetric_2x2(calc):
    put(calc, "D", [[1, 2], [2.1, 5]])
    screen = start(calc, "D")
    i = screen.index("NOT SYMMETRIC:")
    assert re.sub(r"\)[^(]\(", ")≠(", screen[i + 1]) == "(1,2)≠(2,1)", screen
    assert missing(calc, T_LIST, b"\x5dIVAR"), "no results for a rejected tensor"


def test_undefined_matrix_errors(calc):
    start(calc, "E")
    assert calc.error() == "UNDEFINED"


# --- variable safety ----------------------------------------------------------

def test_matrix_and_other_vars_untouched_temps_cleaned(calc):
    put(calc, "A", GENERAL)
    put(calc, "I", [[1, 2], [3, 4]])
    reals = [(b"A", 3), (b"I", 5), (b"J", 6), (b"K", 7), (b"S", 8), (b"X", 9)]
    for v, x in reals:
        calc.send_var(T_REAL, v, tifloat_encode(x))
    run(calc, "A", GENERAL)
    assert decode_matrix(calc.recv_var(T_MATRIX, MAT["A"])) == GENERAL
    assert decode_matrix(calc.recv_var(T_MATRIX, MAT["I"])) == [[1, 2], [3, 4]]
    for v, x in reals:
        assert decode_real(calc.recv_var(T_REAL, v)) == x, v
    for tmp in TEMPS:
        assert missing(calc, T_LIST, b"\x5d" + tmp), "temp list %r left behind" % tmp


def test_temps_cleaned_after_error(calc):
    put(calc, "A", [[1, 2], [3, 4]])
    start(calc, "A")
    for tmp in TEMPS:
        assert missing(calc, T_LIST, b"\x5d" + tmp), "temp list %r left behind" % tmp
