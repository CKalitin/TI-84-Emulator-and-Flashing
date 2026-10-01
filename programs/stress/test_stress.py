"""Emulator tests for STRESS.  Run: ./ti84 test programs/stress"""
import math

from ti84emu import matrix_data, decode_matrix, decode_real, tifloat_encode, T_MATRIX, T_REAL

MAT = {c: bytes([0x5C, i]) for i, c in enumerate("ABCDEFGHIJ")}
LABELS = ["I_1=", "I_2=", "I_3=", "J_2=", "J_3=", "_vM="]  # σ doesn't OCR


def put(calc, name, rows):
    calc.send_var(T_MATRIX, MAT[name], matrix_data(rows))


def reference(rows):
    """I1, I2, I3, J2, J3, von Mises straight from the cheat-sheet formulas."""
    if len(rows) == 2:
        rows = [rows[0] + [0], rows[1] + [0], [0, 0, 0]]
    (sx, txy, txz), (_, sy, tyz), (_, _, sz) = rows
    i1 = sx + sy + sz
    i2 = sx * sy + sy * sz + sz * sx - txy ** 2 - tyz ** 2 - txz ** 2
    i3 = sx * sy * sz + 2 * txy * tyz * txz - sx * tyz ** 2 - sy * txz ** 2 - sz * txy ** 2
    j2 = i1 ** 2 / 3 - i2
    j3 = 2 / 27 * i1 ** 3 - i1 * i2 / 3 + i3
    return [i1, i2, i3, j2, j3, math.sqrt(3 * max(j2, 0))]


def shown(screen):
    """The six numbers on the result screen, in order."""
    out = []
    for label in LABELS:
        row = next((r for r in screen if label in r), None)
        assert row is not None, (label, screen)
        txt = row.split(label, 1)[1].strip().replace("⁻", "-").replace("ᴇ", "e")
        out.append(float(txt))
    return out


def close(got, want):
    """Shown values are rounded to 6 significant figures."""
    for g, w in zip(got, want):
        if abs(w) < 1e-6:
            assert g == 0, (got, want)
        else:
            assert abs(g - w) <= 1e-5 * abs(w), (got, want)


def run(calc, name, rows):
    put(calc, name, rows)
    screen = calc.run_program("STRESS", inputs=[name])
    assert calc.error() is None, screen
    assert screen[0].strip() == "STRESS [%s]" % name, screen
    return screen


def test_general_3x3(calc):
    m = [[50, 30, 20], [30, -20, -10], [20, -10, 10]]
    close(shown(run(calc, "A", m)), reference(m))


def test_uniaxial(calc):
    m = [[100, 0, 0], [0, 0, 0], [0, 0, 0]]
    got = shown(run(calc, "B", m))
    close(got, reference(m))
    assert got[5] == 100, got  # σ_vM = σ for uniaxial


def test_pure_shear(calc):
    m = [[0, 50, 0], [50, 0, 0], [0, 0, 0]]
    got = shown(run(calc, "C", m))
    close(got, reference(m))
    assert abs(got[5] - 50 * math.sqrt(3)) < 1e-3, got


def test_hydrostatic_has_no_deviatoric_part(calc):
    m = [[-30, 0, 0], [0, -30, 0], [0, 0, -30]]
    got = shown(run(calc, "D", m))
    assert got[:3] == [-90, 2700, -27000], got
    assert got[3:] == [0, 0, 0], got  # no round-off noise


def test_hydrostatic_thirds(calc):
    # I1/3 isn't exact in decimal: J2/J3 must still come out exactly 0
    m = [[10, 0, 0], [0, 10, 0], [0, 0, 10]]
    assert shown(run(calc, "E", m))[3:] == [0, 0, 0]


def test_plane_stress_2x2(calc):
    m = [[80, -40], [-40, 20]]
    got = shown(run(calc, "F", m))
    close(got, reference(m))
    assert got[2] == 0, got


def test_pascals_large_and_decimal(calc):
    m = [[125.5e6, -42.25e6, 0], [-42.25e6, -80e6, 15e6], [0, 15e6, 33.3e6]]
    close(shown(run(calc, "J", m)), reference(m))


def test_full_precision_left_in_INV(calc):
    m = [[50, 30, 20], [30, -20, -10], [20, -10, 10]]
    run(calc, "A", m)
    from ti84emu import T_LIST, decode_list
    got = decode_list(calc.recv_var(T_LIST, b"\x5dINV"))
    want = reference(m)
    assert all(abs(g - w) <= 1e-9 * max(1, abs(w)) for g, w in zip(got, want)), (got, want)


def test_negative_signs_display(calc):
    m = [[-50, 0, 0], [0, -20, 0], [0, 0, -10]]
    got = shown(run(calc, "G", m))
    close(got, reference(m))
    assert got[0] == -80 and got[2] == -10000, got


def test_matrix_and_reals_untouched(calc):
    m = [[1, 2, 3], [2, 4, 5], [3, 5, 6]]
    put(calc, "A", [[9, 9], [9, 9]])
    calc.send_var(T_REAL, b"K", tifloat_encode(7))
    run(calc, "H", m)
    assert decode_matrix(calc.recv_var(T_MATRIX, MAT["H"])) == m
    assert decode_matrix(calc.recv_var(T_MATRIX, MAT["A"])) == [[9, 9], [9, 9]]
    assert decode_real(calc.recv_var(T_REAL, b"K")) == 7


def test_not_symmetric(calc):
    put(calc, "A", [[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    screen = calc.run_program("STRESS", inputs=["A"])
    assert "NOT SYMMETRIC" in screen, screen


def test_not_symmetric_2x2(calc):
    put(calc, "A", [[1, 2], [3, 4]])
    screen = calc.run_program("STRESS", inputs=["A"])
    assert "NOT SYMMETRIC" in screen, screen


def test_not_square(calc):
    put(calc, "B", [[1, 2, 3], [4, 5, 6]])
    screen = calc.run_program("STRESS", inputs=["B"])
    assert "NOT SQUARE" in screen, screen


def test_1x1_rejected(calc):
    put(calc, "C", [[5]])
    screen = calc.run_program("STRESS", inputs=["C"])
    assert "NEED 2X2 OR 3X3" in screen, screen


def test_4x4_rejected(calc):
    put(calc, "C", [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    screen = calc.run_program("STRESS", inputs=["C"])
    assert "NEED 2X2 OR 3X3" in screen, screen


def test_bad_name(calc):
    screen = calc.run_program("STRESS", inputs=["K"])
    assert "NAME MUST BE A-J" in screen, screen


def test_two_letters_rejected(calc):
    put(calc, "A", [[1, 0], [0, 1]])
    screen = calc.run_program("STRESS", inputs=["AB"])
    assert "NAME MUST BE A-J" in screen, screen


def test_undefined_matrix_errors(calc):
    # TI-BASIC can't trap this: the OS shows ERR:UNDEFINED
    screen = calc.run_program("STRESS", inputs=["E"])
    assert calc.error() == "UNDEFINED", screen
