"""Emulator tests for BENDING (unsymmetrical bending).  Run: ./ti84 test programs/bending

Worked example: MECH 360 L6 L-channel (Ix 807760, Iy 387760, Ixy 323080 mm^4,
Mx = -100, My = 100 N*m, centroid (11.54, 21.54), points A(-5,-5) B(55,5) D(-5,65)).
`reference()` uses the spec's own forms (alpha = atan((Iu/Iv) tan theta),
sigma = -Mv*u/Iv + Mu*v/Iu, ...) so it is independent of the program's
atan2 / gradient forms.
"""
import math
import os
import re
import struct
import tempfile

from ti84emu import (decode_list, decode_matrix, decode_real, matrix_data, tifloat_encode,
                     T_LIST, T_MATRIX, T_REAL)

HERE = os.path.dirname(os.path.abspath(__file__))
L_SEC = (807760, 387760, 323080, 11.54, 21.54)
L_M = (-100, 100)
L_PTS = [(-5, -5), (55, 5), (-5, 65)]

SEC_LABELS = ["det=", "C=", "R=", "I_u=", "I_v=", "I_u/I_v=", "β="]
INV_LABELS = ["IN11=", "IN12=", "IN22=", "B11=", "B12=", "B21=", "B22="]
MOM_LABELS = ["G_x=", "G_y=", "G_mag=", "M ANG=", "G ANG=", "θ=", "α="]
NA_LABELS = ["NA=", "CHK=", "M_u=", "M_v="]
PT_LABELS = ["r_x=", "r_y=", "u=", "v=", "σ_z=", "CHK="]
TEMPS = [b"BFV", b"BFW", b"BFE", b"BFM", b"BFS", b"BFT", b"BFQ", b"BFN", b"BFZ", b"BK", b"BT"]
POINT_LISTS = [b"BPX", b"BPY", b"BPRX", b"BPRY", b"BPU", b"BPV", b"BPSZ", b"BPCK"]


def wrap180(a):
    return a - 360 * math.ceil((a - 180) / 360)


def wrap90(a):
    return a - 180 * math.ceil((a - 90) / 180)


def reference(sec, m=(0, 0), pts=()):
    ix, iy, ixy, x0, y0 = sec
    det = ix * iy - ixy ** 2
    c0 = (ix + iy) / 2
    r = math.hypot((ix - iy) / 2, ixy)
    if r < 1e-10 * abs(c0):
        r = 0
    iu, iv = c0 + r, c0 - r
    beta = math.degrees(math.atan2(2 * ixy, ix - iy)) / 2 if r else 0
    inv = [iy / det, -ixy / det, ix / det]
    b = [ixy / det, -ix / det, iy / det, -ixy / det]
    out = {"sec": [det, c0, r, iu, iv, iu / iv, beta], "inv": inv + b}
    mx, my = m[0] * 1000, m[1] * 1000
    if not (mx or my):
        return out
    gx, gy = b[0] * mx + b[1] * my + 0.0, b[2] * mx + b[3] * my + 0.0  # no -0.0 on a TI
    ang_m = math.degrees(math.atan2(my, mx))
    ang_g = math.degrees(math.atan2(gy, gx))
    theta = wrap180(ang_m - beta)
    if abs(abs(theta) - 90) < 1e-9:
        alpha = 90.0
    else:
        alpha = wrap90(math.degrees(math.atan(iu / iv * math.tan(math.radians(theta)))))
    c, s = math.cos(math.radians(beta)), math.sin(math.radians(beta))
    mu, mv = c * mx + s * my, -s * mx + c * my
    out["mom"] = [gx, gy, math.hypot(gx, gy), ang_m, ang_g, theta, alpha]
    out["na"] = [wrap90(beta + alpha), wrap90(ang_g - 90), mu / 1000, mv / 1000]
    out["pts"] = []
    for x, y in pts:
        rx, ry = x - x0, y - y0
        u, v = c * rx + s * ry, -s * rx + c * ry
        sz = -mv * u / iv + mu * v / iu
        out["pts"].append([rx, ry, u, v, sz, sz])
    return out


# --- driving the program ------------------------------------------------------

def num(x):
    s = ("%.12f" % abs(x)).rstrip("0").rstrip(".") or "0"
    return ("~" if x < 0 else "") + s


def start(calc, choice, inputs=(), settle=4.0):
    """Launch BENDING, pick 1 (FROM AREAMOM) or 2 (TYPE I VALUES), answer prompts."""
    calc.run_program("BENDING", settle=0.5)
    calc.press("K%d" % choice)
    calc.run(1.5)
    for s in inputs:
        calc.type(s)
        calc.press("ENTER")
        calc.run(1.5)
    calc.run(settle)
    return calc.text()


def n_pages(m, n_pts):
    return 2 if not any(m) else 4 + n_pts + (n_pts > 0)


def pages(calc, first, count, settle=4.0):
    screens = [first]
    assert calc.error() is None, first
    for _ in range(count - 1):
        calc.press("ENTER")
        calc.run(settle)
        screens.append(calc.text())
        assert calc.error() is None, screens[-1]
    return screens


def typed_inputs(sec, m, pts="0"):
    return [num(v) for v in sec] + [num(v) for v in m] + ([pts] if any(m) else [])


def run_typed(calc, sec, m=(0, 0), pts=(), settle=4.0):
    ins = typed_inputs(sec, m, str(len(pts)))
    if any(m):
        ins += [num(v) for p in pts for v in p]
    return pages(calc, start(calc, 2, ins, settle), n_pages(m, len(pts)), settle)


def put(calc, letter, rows):
    calc.send_var(T_MATRIX, bytes([0x5C, "ABCDEFGHIJ".index(letter)]), matrix_data(rows))


def put_list(calc, name, values):
    data = struct.pack("<H", len(values)) + b"".join(tifloat_encode(v) for v in values)
    calc.send_var(T_LIST, b"\x5d" + name, data)


def recv_list(calc, name):
    return decode_list(calc.recv_var(T_LIST, b"\x5d" + name))


def missing(calc, name):
    try:
        calc.recv_var(T_LIST, b"\x5d" + name)
    except Exception:
        return True
    return False


# --- reading the screen -------------------------------------------------------

def label_re(label):
    """Non-ASCII glyphs (β θ α σ) may OCR as anything."""
    return "".join(re.escape(ch) if ord(ch) < 128 else "." for ch in label)


def value(line, label, end=16):
    m = re.match(label_re(label), line)
    assert m, (label, line)
    raw = line[:end]
    assert len(line) >= end and raw[-1] != " ", ("not right-aligned to col %d" % end, line)
    txt = raw[m.end():].strip()
    assert txt and " " not in txt, (label, line)
    return txt


def to_float(txt):
    return float(txt.replace("⁻", "-").replace("ᴇ", "e"))


def shown_close(txt, want, scale=None):
    got = to_float(txt)
    if abs(want) < 1e-10 * (scale or 1):
        assert got == 0, (txt, want)
        return
    mant = re.sub(r"ᴇ.*", "", txt).replace("⁻", "").replace(".", "").lstrip("0")
    if "." in txt or "ᴇ" in txt:
        digits = len(mant)
    else:
        digits = max(len(mant.rstrip("0")), min(len(mant), 6))
    ulp = 10 ** (math.floor(math.log10(abs(got))) - digits + 1)
    assert abs(got - want) <= 0.5 * ulp * 1.0001 + 1e-9 * abs(want), (txt, want)
    assert len(mant) >= 4 or abs(got - want) <= 1e-9 * abs(want), ("too few digits", txt, want)


def angle_close(txt, want):
    """Angles are shown to 0.01°."""
    assert abs(to_float(txt) - round(want, 2)) < 1e-9, (txt, want)


def check_rows(screen, labels, wants, angles=(), first_row=1, scale=None):
    for k, (label, want) in enumerate(zip(labels, wants)):
        line = screen[first_row + k]
        if k in angles:
            angle_close(value(line, label, end=15), want)
            assert line[15:16] not in ("", " "), ("degree sign", line)
        else:
            shown_close(value(line, label), want, scale)


def check_all(screens, ref):
    s = screens[0]
    assert s[0] == "U=STRONG V=WEAK", s
    if ref["sec"][2]:
        check_rows(s, SEC_LABELS, ref["sec"], angles=(6,))
    else:
        check_rows(s, SEC_LABELS[:6], ref["sec"][:6], scale=ref["sec"][1])
        assert s[7].replace(" ", "")[2:] == "ANYAXIS", s
    s = screens[1]
    assert s[0].startswith("IN=INV(I),1/MM"), s
    check_rows(s, INV_LABELS, ref["inv"], scale=max(abs(v) for v in ref["inv"]))
    if "mom" not in ref:
        assert len(screens) == 2
        return
    s = screens[2]
    assert s[0][:5] == "GRAD " and s[0][6:] == "_z, MPA/MM", s
    gscale = ref["mom"][2]
    check_rows(s, MOM_LABELS, ref["mom"], angles=(3, 4, 5, 6), scale=gscale)
    s = screens[3]
    assert s[0] == "NEUTRAL AXIS", s
    check_rows(s, NA_LABELS, ref["na"], angles=(0, 1), scale=max(map(abs, ref["na"][2:])))
    assert s[5] == "(M_u,M_v: N*M)" and s[7] == "NA,ANG:CCW FRM X", s
    pts = ref["pts"]
    if not pts:
        assert len(screens) == 4
        return
    sz = [p[4] for p in pts]
    imax = max(range(len(sz)), key=lambda i: (abs(sz[i]), -i))
    for i, p in enumerate(pts):
        s = screens[4 + i]
        assert s[0].replace(" ", "").startswith("POINT%d" % (i + 1)), s
        assert s[0].endswith("MAX") == (i == imax), s
        check_rows(s, PT_LABELS, p, scale=max(map(abs, sz)) or 1)
        want = "MPA, TENSION" if p[4] > 0 else "MPA, COMPRESSION" if p[4] < 0 else "MPA, ZERO"
        assert s[7] == want, s
    s = screens[4 + len(pts)]
    assert s[0][:7] == "MAX ABS", s
    assert value(s[2], "POINT=") == str(imax + 1), s
    shown_close(value(s[3], "σ_z="), sz[imax])


# --- MECH 360 worked example --------------------------------------------------

def test_L_channel_matches_spec(calc):
    screens = run_typed(calc, L_SEC, L_M, L_PTS)
    ref = reference(L_SEC, L_M, L_PTS)
    check_all(screens, ref)
    # spec's expected values, as printed
    s0, s2, s3 = screens[0], screens[2], screens[3]
    assert value(s0[4], "I_u=").startswith("983092") and value(s0[5], "I_v=").startswith("212428"), s0
    assert value(s0[7], "β=", 15) == "28.49", s0
    assert value(s2[5], "G ANG=", 15) == "⁻147.85", s2
    assert value(s2[6], "θ=", 15) == "106.51" and value(s2[7], "α=", 15) == "⁻86.34", s2
    assert value(s3[1], "NA=", 15) == "⁻57.85" and value(s3[2], "CHK=", 15) == "⁻57.85", s3
    assert value(s3[3], "M_u=").startswith("⁻40.19") and value(s3[4], "M_v=").startswith("135.58"), s3
    a, b, d = screens[4:7]
    assert value(a[3], "u=").startswith("⁻27.196") and value(a[4], "v=").startswith("⁻15.437"), a
    assert value(a[5], "σ_z=").startswith("17.99") and a[0].endswith("MAX"), a
    assert value(b[3], "u=").startswith("30.308") and value(b[4], "v=").startswith("⁻35.26"), b
    assert value(b[5], "σ_z=").startswith("⁻17.90"), b
    assert value(d[5], "σ_z=").startswith("⁻5.836"), d


def test_results_lists_full_precision(calc):
    run_typed(calc, L_SEC, L_M, L_PTS)
    ref = reference(L_SEC, L_M, L_PTS)
    sec = recv_list(calc, b"BSEC")
    assert len(sec) == 12, sec
    for g, w in zip(sec[:5] + sec[5:], list(L_SEC) + ref["sec"][:6] + ref["sec"][6:]):
        assert abs(g - w) <= 1e-9 * max(1, abs(w)), (sec, ref["sec"])
    inv = recv_list(calc, b"BINV")
    assert all(abs(g - w) <= 1e-9 * abs(w) for g, w in zip(inv, ref["inv"])), inv
    mom = recv_list(calc, b"BMOM")
    want = list(L_M) + ref["mom"] + ref["na"]
    assert len(mom) == 13, mom
    assert all(abs(g - w) <= 1e-8 * max(1, abs(w)) for g, w in zip(mom, want)), (mom, want)
    sz = recv_list(calc, b"BPSZ")
    assert all(abs(g - p[4]) <= 1e-9 * abs(p[4]) for g, p in zip(sz, ref["pts"])), sz


def test_points_from_matrix_same_as_typed(calc):
    typed = run_typed(calc, L_SEC, L_M, L_PTS)
    calc.press("CLEAR")
    put(calc, "B", [list(p) for p in L_PTS])
    ins = typed_inputs(L_SEC, L_M, "B")
    by_matrix = pages(calc, start(calc, 2, ins), n_pages(L_M, 3))
    assert by_matrix == typed, (by_matrix, typed)
    assert decode_matrix(calc.recv_var(T_MATRIX, b"\x5c\x01")) == [list(p) for p in L_PTS]


def test_from_areamom_results_list(calc):
    # AREAMOM's ʟMOA = {A, x0*, y0*, Ix, Iy, Ixy, I_O, R, I_str, I_wk, beta}
    put_list(calc, b"MOA", [1300, 11.5385, 21.5385, 807756, 387756, 323077, 0, 0, 0, 0, 0])
    sec = (807756, 387756, 323077, 11.5385, 21.5385)
    put(calc, "A", [list(p) for p in L_PTS])
    screens = pages(calc, start(calc, 1, [num(v) for v in L_M] + ["A"]), n_pages(L_M, 3))
    check_all(screens, reference(sec, L_M, L_PTS))


def test_after_running_areamom(calc):
    from tibasic import compile_file
    calc.send_file(compile_file(os.path.join(HERE, "..", "areamom", "AREAMOM.bas"),
                                tempfile.mkdtemp()))
    calc.run_program("AREAMOM", settle=0.5)
    calc.press("K3")  # TYPE CENTROIDS
    calc.run(1.5)
    for v in ["2", "10", "80", "0", "35", "50", "10", "30", "0"]:
        calc.type(v + "\n")
        calc.run(1.5)
    calc.run(4)
    for _ in range(3):
        calc.press("ENTER")
        calc.run(4)
    moa = recv_list(calc, b"MOA")
    calc.press("CLEAR")
    pts = [(-5, -5), (55, 5), (-5, 65)]
    screens = pages(calc, start(calc, 1, [num(v) for v in L_M] + ["3"] + [num(v) for p in pts for v in p]),
                    n_pages(L_M, 3))
    check_all(screens, reference((moa[3], moa[4], moa[5], moa[1], moa[2]), L_M, pts))
    assert value(screens[4][5], "σ_z=").startswith("17.9"), screens[4]


# --- special cases ------------------------------------------------------------

def test_section_only_when_no_moment(calc):
    screens = run_typed(calc, L_SEC, (0, 0))
    check_all(screens, reference(L_SEC))
    assert calc.text() == screens[1]
    for name in POINT_LISTS:
        assert missing(calc, name), name


def test_moment_without_points(calc):
    screens = run_typed(calc, L_SEC, L_M, [])
    check_all(screens, reference(L_SEC, L_M))


def test_symmetric_section_x_moment(calc):
    sec = (8e6, 2e6, 0, 0, 0)
    screens = run_typed(calc, sec, (5, 0), [(0, 100), (40, -100)])
    check_all(screens, reference(sec, (5, 0), [(0, 100), (40, -100)]))
    assert value(screens[0][7], "β=", 15) == "0", screens[0]
    assert value(screens[3][1], "NA=", 15) == "0", screens[3]  # N.A. along x
    assert screens[4][7] == "MPA, TENSION", screens[4]   # course sign: sigma = Mx*y/Ix


def test_moment_along_weak_axis_theta_90(calc):
    sec = (8e6, 2e6, 0, 0, 0)
    for m in [(0, 3), (0, -3)]:
        calc.press("CLEAR")
        screens = run_typed(calc, sec, m, [(50, 0)])
        check_all(screens, reference(sec, m, [(50, 0)]))
        assert value(screens[3][1], "NA=", 15) == "90", screens[3]
        assert value(screens[3][2], "CHK=", 15) == "90", screens[3]


def test_equal_principal_any_axis(calc):
    sec = (5e5, 5e5, 0, 0, 0)
    screens = run_typed(calc, sec, (1, 1), [(10, 10)])
    check_all(screens, reference(sec, (1, 1), [(10, 10)]))


def test_point_at_centroid_is_zero(calc):
    screens = run_typed(calc, L_SEC, L_M, [(11.54, 21.54), (-5, -5)])
    assert screens[4][7] == "MPA, ZERO", screens[4]
    assert screens[5][0].endswith("MAX"), screens[5]


def test_radian_mode_still_gives_degrees(calc):
    from tibasic import compile_source
    p = compile_source("Radian", "SETRAD")
    path = os.path.join(tempfile.mkdtemp(), "SETRAD.8xp")
    p.save(path)
    calc.send_file(path)
    calc.run_program("SETRAD")
    screens = run_typed(calc, L_SEC, L_M, L_PTS)
    check_all(screens, reference(L_SEC, L_M, L_PTS))


def test_expressions_accepted(calc):
    ins = ["807760", "387760", "323080", "1154/100", "2154/100", "~200/2", "50*2", "0"]
    s = start(calc, 2, ins)
    assert calc.error() is None, s
    assert value(s[7], "β=", 15) == "28.49", s


# --- input checking -----------------------------------------------------------

def test_menu(calc):
    s = calc.run_program("BENDING", settle=0.5)
    assert s[0].strip() == "UNSYM BENDING", s
    assert s[1] == "1:FROM AREAMOM" and s[2] == "2:TYPE I VALUES", s


def test_not_positive_definite_rejected(calc):
    s = start(calc, 2, ["100", "100", "200", "0", "0"])
    assert calc.error() is None, s
    assert "NOT A REAL" in s, s


def test_points_matrix_wrong_columns(calc):
    put(calc, "C", [[1, 2, 3]])
    s = start(calc, 2, typed_inputs(L_SEC, L_M, "C"))
    assert "NEED 2 COLUMNS:" in s, s


def test_points_bad_entry(calc):
    for bad, msg in [("K", "A-J OR A NUMBER"), ("1.5", "NEED 0-99 POINTS"), ("100", "NEED 0-99 POINTS")]:
        calc.press("CLEAR")
        s = start(calc, 2, typed_inputs(L_SEC, L_M, bad))
        assert calc.error() is None, s
        assert msg in s, (bad, s)


def test_points_matrix_undefined(calc):
    start(calc, 2, typed_inputs(L_SEC, L_M, "J"))
    assert calc.error() == "UNDEFINED"


def test_from_areamom_without_MOA_errors(calc):
    start(calc, 1)
    assert calc.error() == "UNDEFINED"


# --- variable safety ----------------------------------------------------------

def test_other_vars_untouched_and_temps_cleaned(calc):
    put(calc, "A", [[1, 2], [3, 4]])
    reals = [(b"A", 3), (b"B", 4), (b"C", 5), (b"K", 6), (b"R", 7), (b"X", 8), (b"Y", 9), (b"\x5b", 2)]
    for v, x in reals:
        calc.send_var(T_REAL, v, tifloat_encode(x))
    run_typed(calc, L_SEC, L_M, L_PTS)
    assert decode_matrix(calc.recv_var(T_MATRIX, b"\x5c\x00")) == [[1, 2], [3, 4]]
    for v, x in reals:
        assert decode_real(calc.recv_var(T_REAL, v)) == x, v
    for name in TEMPS:
        assert missing(calc, name), "temp list %r left behind" % name
