"""Headless TI-84 Plus emulator driver (TilEm core via libtihl.so).

Everything is programmatic: no GUI, no X server.
  - boot the real ROM dumped from the user's calculator
  - send/receive variables over the emulated link port (TI DBUS protocol)
  - press physical keys (scancodes), type text
  - read the LCD as pixels, ASCII art, PNG, or OCR'd text
"""
import ctypes
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_ROM = os.path.join(ROOT, "ti84p_dump.rom")

_L = ctypes.CDLL(os.path.join(HERE, "libtihl.so"))
_P, _I, _S = ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
for name, args, res in [
    ("th_open", [_S, _S], _P), ("th_save", [_P, _S, _S], _I), ("th_close", [_P], None),
    ("th_run", [_P, _I], ctypes.c_uint), ("th_key_down", [_P, _I], None),
    ("th_key_up", [_P, _I], None), ("th_asleep", [_P], _I),
    ("th_send_byte", [_P, _I, _I], _I), ("th_get_byte", [_P, _I], _I),
    ("th_link_reset", [_P], None), ("th_lcd", [_P, _S], None), ("th_lcd_on", [_P], _I),
    ("th_pc", [_P], _I), ("th_read_mem", [_P, _I], _I), ("th_set_verbose", [_I], None),
]:
    f = getattr(_L, name)
    f.argtypes, f.restype = args, res

# ---------------------------------------------------------------- keys
K = dict(
    DOWN=0x01, LEFT=0x02, RIGHT=0x03, UP=0x04, ENTER=0x09, ADD=0x0A, SUB=0x0B,
    MUL=0x0C, DIV=0x0D, POWER=0x0E, CLEAR=0x0F, CHS=0x11, K3=0x12, K6=0x13,
    K9=0x14, RPAREN=0x15, TAN=0x16, VARS=0x17, DECPNT=0x19, K2=0x1A, K5=0x1B,
    K8=0x1C, LPAREN=0x1D, COS=0x1E, PRGM=0x1F, STAT=0x20, K0=0x21, K1=0x22,
    K4=0x23, K7=0x24, COMMA=0x25, SIN=0x26, APPS=0x27, XTON=0x28, ON=0x29,
    STORE=0x2A, LN=0x2B, LOG=0x2C, SQUARE=0x2D, RECIP=0x2E, MATH=0x2F,
    ALPHA=0x30, GRAPH=0x31, TRACE=0x32, ZOOM=0x33, WINDOW=0x34, YEQU=0x35,
    SECOND=0x36, MODE=0x37, DEL=0x38,
)
_ALPHA_KEYS = "MATH APPS PRGM RECIP SIN COS TAN POWER SQUARE COMMA LPAREN RPAREN DIV " \
              "LOG K7 K8 K9 MUL LN K4 K5 K6 SUB STORE K1 K2 K3".split()
# Keystroke sequences for characters typed at the home screen / an Input prompt.
CHAR_KEYS = {c: ["ALPHA", k] for c, k in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZθ", _ALPHA_KEYS)}
CHAR_KEYS.update({str(d): ["K%d" % d] for d in range(10)})
CHAR_KEYS.update({
    ".": ["DECPNT"], "+": ["ADD"], "*": ["MUL"], "/": ["DIV"], "^": ["POWER"],
    "(": ["LPAREN"], ")": ["RPAREN"], ",": ["COMMA"], "~": ["CHS"],  # ~ = negative sign
    "-": ["SUB"], "→": ["STORE"], " ": ["ALPHA", "K0"], '"': ["ALPHA", "ADD"],
    ":": ["ALPHA", "DECPNT"], "?": ["ALPHA", "CHS"],
    "{": ["SECOND", "LPAREN"], "}": ["SECOND", "RPAREN"],
    "[": ["SECOND", "MUL"], "]": ["SECOND", "SUB"], "\n": ["ENTER"],
})

# ---------------------------------------------------------------- DBUS
PC, CALC = 0x23, 0x73
VAR, CTS, XDP, SKP, ACK, ERR, RDY, EOT, REQ, RTS = (
    0x06, 0x09, 0x15, 0x36, 0x56, 0x5A, 0x68, 0x92, 0xA2, 0xC9)
_DATA_CMDS = {VAR, XDP, SKP, 0xA2, 0xC9, 0x47}

# variable type ids
T_REAL, T_LIST, T_MATRIX, T_STRING, T_PROG, T_PPROG = 0x00, 0x01, 0x02, 0x04, 0x05, 0x06


class LinkError(Exception):
    pass


class ProgramError(Exception):
    pass


class TI84:
    """One emulated TI-84 Plus. Emulated time only advances when we run it."""

    def __init__(self, rom=DEFAULT_ROM, sav=None, boot=True):
        self.c = _L.th_open(rom.encode(), sav.encode() if sav else None)
        if not self.c:
            raise RuntimeError("could not load ROM %s" % rom)
        if boot and sav is None:
            self.run(2.0)
            self.press("ON", hold=0.3)
            self.run(1.0)
            self.press("CLEAR")

    def close(self):
        if self.c:
            _L.th_close(self.c)
            self.c = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def save(self, rom_path, sav_path):
        if _L.th_save(self.c, rom_path.encode(), sav_path.encode()):
            raise RuntimeError("save failed")

    # ---- time / keys
    def run(self, seconds):
        _L.th_run(self.c, int(seconds * 1e6))

    def press(self, key, hold=0.1, after=0.6):
        _L.th_key_down(self.c, K[key])
        self.run(hold)
        _L.th_key_up(self.c, K[key])
        self.run(after)

    def keys(self, *names):
        for n in names:
            self.press(n)

    def type(self, text):
        """Type characters (see CHAR_KEYS). Uppercase letters only."""
        for ch in text:
            if ch not in CHAR_KEYS:
                raise KeyError("no keystroke for %r" % ch)
            self.keys(*CHAR_KEYS[ch])

    # ---- LCD
    def pixels(self):
        b = ctypes.create_string_buffer(96 * 64)
        _L.th_lcd(self.c, b)
        return b.raw

    def ascii(self):
        p = self.pixels()
        return "\n".join("".join("#" if p[y * 96 + x] else "." for x in range(96)) for y in range(64))

    def png(self, path, scale=4):
        return write_png(self.pixels(), path, scale)

    def text(self):
        """OCR the home screen (8 rows x 16 cols, large font). Needs font.json."""
        from ocr import read_screen
        return read_screen(self.pixels())

    # ---- link layer
    def _send(self, cmd, data=None):
        pkt = bytes([PC, cmd])
        if data is None:
            pkt += b"\x00\x00"
        else:
            pkt += struct.pack("<H", len(data)) + data + struct.pack("<H", sum(data) & 0xFFFF)
        for b in pkt:
            r = _L.th_send_byte(self.c, b, 2_000_000)
            if r < 0:
                raise LinkError("send byte failed (%d) on cmd %02X" % (r, cmd))

    def _byte(self, timeout=5.0):
        v = _L.th_get_byte(self.c, int(timeout * 1e6))
        if v < 0:
            raise LinkError("timeout waiting for byte (%d)" % v)
        return v

    def _recv(self, timeout=5.0):
        mid, cmd = self._byte(timeout), self._byte()
        n = self._byte() | (self._byte() << 8)
        data = b""
        if cmd in _DATA_CMDS:
            data = bytes(self._byte() for _ in range(n))
            ck = self._byte() | (self._byte() << 8)
            if ck != sum(data) & 0xFFFF:
                raise LinkError("bad checksum")
        return cmd, n, data

    def _expect(self, want, timeout=5.0):
        cmd, n, data = self._recv(timeout)
        if cmd != want:
            raise LinkError("expected %02X, got %02X (len %d, %s)" % (want, cmd, n, data.hex()))
        return n, data

    @staticmethod
    def _hdr(size, vtype, name, attr=0):
        name = name.ljust(8, b"\x00")[:8]
        return struct.pack("<HB", size, vtype) + name + bytes([0, 0x80 if attr else 0])

    def send_var(self, vtype, name, data, archived=False):
        """Silent-link send of one variable (raw var data, incl. any length prefix)."""
        self._send(RTS, self._hdr(len(data), vtype, name, archived))
        self._expect(ACK)
        cmd, n, d = self._recv(10.0)
        if cmd == SKP:
            raise LinkError("calculator rejected variable %r (code %s)" % (name, d.hex()))
        if cmd != CTS:
            raise LinkError("expected CTS, got %02X" % cmd)
        self._send(ACK)
        self._send(XDP, data)
        self._expect(ACK)
        self._send(EOT)
        self.run(0.3)

    def recv_var(self, vtype, name):
        """Silent-link request of one variable; returns raw var data."""
        self._send(REQ, self._hdr(0, vtype, name))
        self._expect(ACK)
        cmd, n, hdr = self._recv(10.0)
        if cmd == SKP:
            raise LinkError("variable %r not found (code %s)" % (name, hdr.hex()))
        if cmd != VAR:
            raise LinkError("expected VAR, got %02X" % cmd)
        self._send(ACK)
        self._send(CTS)
        self._expect(ACK)
        _, data = self._expect(XDP, 10.0)
        self._send(ACK)
        self.run(0.3)
        return data

    def send_file(self, path):
        """Send every variable in a .8x? file."""
        for vtype, name, data, arch in read_8x(path):
            self.send_var(vtype, name, data, arch)

    # ---- high level
    def run_program(self, name, inputs=(), settle=5.0, input_wait=1.5):
        """Launch prgmNAME from the home screen, answer prompts, return screen text.

        `inputs` are strings typed (via CHAR_KEYS) then ENTER, one per prompt.
        """
        name = name.upper()
        self.keys("SECOND", "MODE", "CLEAR", "CLEAR")   # QUIT to a clean home screen
        self.press("PRGM")
        menu = self.text()
        idx = next((i for i, l in enumerate(menu[1:], 1) if l[2:] == name), None)
        if idx is None:
            raise ProgramError("program %s not visible in PRGM menu: %r" % (name, menu))
        for _ in range(idx - 1):
            self.press("DOWN")
        self.keys("ENTER", "ENTER")
        self.run(input_wait)
        for s in inputs:
            self.type(s)
            self.press("ENTER")
            self.run(input_wait)
        self.run(settle)
        return self.text()

    def error(self):
        """'SYNTAX', 'UNDEFINED', ... if an ERR: screen is showing, else None."""
        first = self.text()[0]
        return first[4:].strip() if first.startswith("ERR:") else None

    def goto_error(self):
        """From an ERR: screen choose Goto. Returns (editor_lines, (row, col)):
        the program-editor screen text and the blinking cursor cell, which sits
        on the offending token (None if not found)."""
        self.press("K2")
        self.run(1.0)
        frames = []
        for _ in range(12):
            self.run(0.1)
            frames.append(self.pixels())
        cur = None
        for r in range(8):
            for c in range(16):
                cells = {bytes(f[(r * 8 + y) * 96 + c * 6 + x] for y in range(8) for x in range(6))
                         for f in frames}
                if len(cells) > 1:
                    cur = cur or (r, c)
        # read text with the cursor off if possible
        from ocr import read_screen
        texts = [read_screen(f) for f in frames]
        lines = min(texts, key=lambda t: sum(l.count("█") for l in t))
        return lines, cur


# ---------------------------------------------------------------- files
def write_png(px, path, scale=4):
    """Write 96x64 0/1 pixels as an LCD-coloured PNG."""
    on, off = (0, 0, 0), (0xC6, 0xD3, 0xB8)
    rows = []
    for y in range(64):
        row = b"".join(bytes(on if px[y * 96 + x] else off) * scale for x in range(96))
        rows += [b"\x00" + row] * scale
    w, h = 96 * scale, 64 * scale

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(b"".join(rows))) + chunk(b"IEND", b""))
    return path


def read_8x(path):
    """Yield (type, name, data, archived) for each var entry in a .8x? file."""
    raw = open(path, "rb").read()
    if raw[:8] != b"**TI83F*":
        raise ValueError("not a TI-83+/84+ file: %s" % path)
    body_len = struct.unpack_from("<H", raw, 53)[0]
    body, i = raw[55:55 + body_len], 0
    while i < len(body):
        hlen, dlen, vtype = struct.unpack_from("<HHB", body, i)
        name = body[i + 5:i + 13].rstrip(b"\x00")
        arch = hlen >= 13 and body[i + 14] & 0x80
        data = body[i + 2 + hlen + 2:i + 2 + hlen + 2 + dlen]
        yield vtype, name, data, bool(arch)
        i += 2 + hlen + 2 + dlen


def tifloat_decode(b):
    """Decode a 9-byte TI real float."""
    sign = -1 if b[0] & 0x80 else 1
    exp = b[1] - 0x80
    digits = "".join("%02x" % x for x in b[2:9])
    return sign * int(digits) * 10.0 ** (exp - 13)


def tifloat_encode(v):
    if v == 0:
        return bytes([0, 0x80]) + bytes(7)
    s = "%.13e" % abs(v)
    mant, exp = s.split("e")
    digits = mant.replace(".", "").ljust(14, "0")
    return bytes([0x80 if v < 0 else 0, 0x80 + int(exp)]) + bytes.fromhex(digits)


def matrix_data(rows):
    """Var data for a real matrix [[...],[...]]."""
    out = bytes([len(rows[0]), len(rows)])
    return out + b"".join(tifloat_encode(v) for r in rows for v in r)


def decode_real(data):
    return tifloat_decode(data[:9])


def decode_list(data):
    n = struct.unpack_from("<H", data)[0]
    return [tifloat_decode(data[2 + 9 * i:11 + 9 * i]) for i in range(n)]


def decode_matrix(data):
    cols, rows = data[0], data[1]
    v = [tifloat_decode(data[2 + 9 * i:11 + 9 * i]) for i in range(rows * cols)]
    return [v[r * cols:(r + 1) * cols] for r in range(rows)]
