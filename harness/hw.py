"""Talk to the real TI-84 Plus over USB (DUSB protocol), so programs can be
verified on hardware without a human in the loop: send, launch, type input,
screenshot + OCR the real LCD, and read variables back.

Built on the DUSB transport in romdump.py (a from-scratch reimplementation of
tilibs' protocol; the packaged libticables fails on this machine).

  ./ti84 hw ping
  ./ti84 hw screen [out.png]
  ./ti84 hw send FILE.8xp|FILE.bas ...
  ./ti84 hw get matrix A | real T | list 1 | program NAME
  ./ti84 hw keys "TEXT"                     (\\n = ENTER)
  ./ti84 hw run NAME [-i INPUT ...] [--wait S]
"""
import argparse
import os
import time

import romdump
from romdump import Link, ProtocolError
from ti84emu import (T_LIST, T_MATRIX, T_PROG, T_REAL, decode_list, decode_matrix,
                     decode_real, read_8x, write_png)

VPKT_PARM_REQ, VPKT_PARM_DATA = 0x0007, 0x0008
VPKT_VAR_HDR, VPKT_RTS, VPKT_VAR_REQ, VPKT_VAR_CNTS = 0x000A, 0x000B, 0x000C, 0x000D
VPKT_EXECUTE, VPKT_DATA_ACK, VPKT_DELAY_ACK, VPKT_EOT, VPKT_ERROR = 0x0011, 0xAA00, 0xBB00, 0xDD00, 0xEE00
PID_SCREENSHOT = 0x0022
EID_PRGM, EID_KEY = 0x00, 0x03
AID_VAR_SIZE, AID_VAR_TYPE, AID_ARCHIVED, AID_VAR_VERSION, AID_DATATYPE = 0x01, 0x02, 0x03, 0x08, 0x11

# TI-OS keycodes (ti83plus.inc k* values) for remote keypresses
KEYCODE = {chr(ord("A") + i): 0x9A + i for i in range(26)}
KEYCODE.update({str(i): 0x8E + i for i in range(10)})
KEYCODE.update({
    "+": 0x80, "-": 0x81, "*": 0x82, "/": 0x83, "^": 0x84, "(": 0x85, ")": 0x86,
    "[": 0x87, "]": 0x88, "→": 0x8A, ",": 0x8B, "~": 0x8C, ".": 0x8D, " ": 0x99,
    ":": 0xC6, "?": 0xCA, '"': 0xCB, "θ": 0xCC, "{": 0xEC, "}": 0xED, "\n": 0x05,
})
K_ENTER, K_CLEAR, K_QUIT, K_PRGM_TOKEN = 0x05, 0x09, 0x40, 0xDA


class Calc:
    def __init__(self):
        self.link = Link()
        self.link.mode_set_ping()

    def close(self):
        self.link.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    # ---- virtual packets
    def _send(self, vtype, data):
        self.link.dusb_send_data(vtype, data)

    def _recv(self, *want, allow_delay=True):
        while True:
            vtype, data = self.link.dusb_recv_data()
            if vtype == VPKT_DELAY_ACK and allow_delay and VPKT_DELAY_ACK not in want:
                delay = int.from_bytes(data[0:4], "big")
                time.sleep(min(delay, 400000) / 1e6)
                continue
            if vtype == VPKT_ERROR:
                raise ProtocolError("calculator error 0x%s" % data.hex())
            if want and vtype not in want:
                raise ProtocolError("expected %s, got 0x%04x" % ([hex(w) for w in want], vtype))
            return vtype, data

    @staticmethod
    def _name(name):
        return bytes([len(name)]) + name + b"\x00"

    @staticmethod
    def _attrs(attrs):
        out = len(attrs).to_bytes(2, "big")
        for aid, val in attrs:
            out += aid.to_bytes(2, "big") + len(val).to_bytes(2, "big") + val
        return out

    # ---- operations
    def send_var(self, vtype, name, data, archived=False):
        hdr = (b"\x00" + self._name(name) + len(data).to_bytes(4, "big") + b"\x01"
               + self._attrs([(AID_VAR_TYPE, bytes([0xF0, 0x0B, 0x00, vtype])),
                              (AID_ARCHIVED, bytes([1 if archived else 0])),
                              (AID_VAR_VERSION, bytes(4))]))
        self._send(VPKT_RTS, hdr)
        self._recv(VPKT_DATA_ACK)
        self._send(VPKT_VAR_CNTS, data)
        self._recv(VPKT_DATA_ACK)
        self._send(VPKT_EOT, b"")
        time.sleep(0.05)

    def send_file(self, path):
        for vtype, name, data, arch in read_8x(path):
            self.send_var(vtype, name, data, arch)

    def recv_var(self, vtype, name):
        aids = [AID_ARCHIVED, AID_VAR_VERSION, AID_VAR_SIZE]
        req = (b"\x00" + self._name(name) + b"\x01\xff\xff\xff\xff"
               + len(aids).to_bytes(2, "big") + b"".join(a.to_bytes(2, "big") for a in aids)
               + self._attrs([(AID_DATATYPE, bytes([0xF0, 0x07, 0x00, vtype]))]) + b"\x00\x00")
        self._send(VPKT_VAR_REQ, req)
        self._recv(VPKT_VAR_HDR)
        _, data = self._recv(VPKT_VAR_CNTS)
        return data

    def screenshot(self):
        """96*64 list of 0/1 pixels from the real LCD."""
        self._send(VPKT_PARM_REQ, (1).to_bytes(2, "big") + PID_SCREENSHOT.to_bytes(2, "big"))
        _, data = self._recv(VPKT_PARM_DATA)
        bm = data[7:]
        if len(bm) != 768:
            raise ProtocolError("unexpected screenshot size %d" % len(bm))
        return bytes((bm[y * 12 + x // 8] >> (7 - x % 8)) & 1 for y in range(64) for x in range(96))

    def text(self):
        from ocr import read_screen
        return read_screen(self.screenshot())

    def key(self, code):
        arg = bytes([0, code]) if code < 0x100 else bytes([code & 0xFF, code >> 8])
        self._send(VPKT_EXECUTE, b"\x00\x00" + bytes([EID_KEY]) + arg)
        self._recv(VPKT_DELAY_ACK, allow_delay=False)
        self._recv(VPKT_DATA_ACK)

    def type(self, text):
        for ch in text:
            self.key(KEYCODE[ch])

    def run_program(self, name, inputs=(), wait=3.0, input_wait=1.0):
        """Same keystrokes a person would use: QUIT, CLEAR, prgmNAME, ENTER."""
        self.key(K_QUIT)
        self.key(K_CLEAR)
        self.key(K_PRGM_TOKEN)
        self.type(name.upper())
        self.key(K_ENTER)
        time.sleep(input_wait)
        for s in inputs:
            self.type(s)
            self.key(K_ENTER)
            time.sleep(input_wait)
        time.sleep(wait)
        return self.text()


VARTYPES = {"real": T_REAL, "list": T_LIST, "matrix": T_MATRIX, "program": T_PROG}


def var_name(kind, name):
    if kind == "matrix":
        return bytes([0x5C, "ABCDEFGHIJ".index(name.upper())])
    if kind == "list":
        return bytes([0x5D, int(name) - 1])
    return name.upper().encode()


def main(argv):
    ap = argparse.ArgumentParser(prog="ti84 hw")
    ap.add_argument("-v", action="store_true", help="log every USB packet")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("ping")
    p = sp.add_parser("screen"); p.add_argument("png", nargs="?")
    p = sp.add_parser("send"); p.add_argument("files", nargs="+")
    p = sp.add_parser("get"); p.add_argument("kind", choices=VARTYPES); p.add_argument("name")
    p = sp.add_parser("keys"); p.add_argument("text")
    p = sp.add_parser("run"); p.add_argument("name")
    p.add_argument("-i", "--input", action="append", default=[])
    p.add_argument("--wait", type=float, default=3.0)
    a = ap.parse_args(argv)
    romdump.VERBOSE = a.v

    with Calc() as calc:
        if a.cmd == "ping":
            print("calculator connected and responding")
        elif a.cmd == "screen":
            px = calc.screenshot()
            from ocr import read_screen
            print("\n".join("|%-16s|" % l for l in read_screen(px)))
            if a.png:
                print("screenshot:", write_png(px, a.png))
        elif a.cmd == "send":
            from tibasic import compile_file
            for f in a.files:
                if f.endswith(".bas"):
                    f = compile_file(f)
                calc.send_file(f)
                print("sent", f)
        elif a.cmd == "get":
            data = calc.recv_var(VARTYPES[a.kind], var_name(a.kind, a.name))
            dec = {"real": decode_real, "list": decode_list, "matrix": decode_matrix}.get(a.kind)
            print(dec(data) if dec else data.hex())
        elif a.cmd == "keys":
            calc.type(a.text.replace("\\n", "\n"))
        elif a.cmd == "run":
            screen = calc.run_program(a.name, a.input, a.wait)
            print("\n".join("|%-16s|" % l for l in screen))
            out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "out", "HW_%s.png" % a.name.upper())
            os.makedirs(os.path.dirname(out), exist_ok=True)
            print("screenshot:", write_png(calc.screenshot(), out))
    return 0
