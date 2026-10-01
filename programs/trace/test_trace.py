"""Emulator tests for TRACE.  Run: ./ti84 test programs/trace"""
from ti84emu import matrix_data, T_MATRIX, T_REAL, tifloat_encode

MAT = {c: bytes([0x5C, i]) for i, c in enumerate("ABCDEFGHIJ")}


def put(calc, name, rows):
    calc.send_var(T_MATRIX, MAT[name], matrix_data(rows))


def result(screen):
    """The number Disp'd under 'TRACE:'."""
    assert "TRACE:" in screen, screen
    return screen[screen.index("TRACE:") + 1].strip()


def test_2x2(calc):
    put(calc, "A", [[1, 2], [3, 4]])
    screen = calc.run_program("TRACE", inputs=["A"])
    assert calc.error() is None, screen
    assert result(screen) == "5", screen


def test_3x3_negative_decimal(calc):
    put(calc, "C", [[1.5, 9, 9], [9, -4, 9], [9, 9, 0.25]])
    screen = calc.run_program("TRACE", inputs=["C"])
    assert result(screen) == "⁻2.25", screen


def test_1x1_matrix_J(calc):
    put(calc, "J", [[7]])
    screen = calc.run_program("TRACE", inputs=["J"])
    assert result(screen) == "7", screen


def test_other_matrices_untouched(calc):
    put(calc, "A", [[1, 2], [3, 4]])
    put(calc, "B", [[5, 6], [7, 8]])
    screen = calc.run_program("TRACE", inputs=["B"])
    assert result(screen) == "13", screen
    from ti84emu import decode_matrix
    assert decode_matrix(calc.recv_var(T_MATRIX, MAT["A"])) == [[1, 2], [3, 4]]


def test_not_square(calc):
    put(calc, "D", [[1, 2, 3], [4, 5, 6]])
    screen = calc.run_program("TRACE", inputs=["D"])
    assert "NOT SQUARE" in screen, screen


def test_bad_name(calc):
    screen = calc.run_program("TRACE", inputs=["K"])
    assert "NAME MUST BE A-J" in screen, screen


def test_two_letters_rejected(calc):
    screen = calc.run_program("TRACE", inputs=["AB"])
    assert "NAME MUST BE A-J" in screen, screen


def test_previous_A_defined_does_not_matter(calc):
    # the original bug: real var A existed on hardware
    calc.send_var(T_REAL, b"A", tifloat_encode(3))
    put(calc, "A", [[2, 0], [0, 2]])
    screen = calc.run_program("TRACE", inputs=["A"])
    assert result(screen) == "4", screen
