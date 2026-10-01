# TI-84 Plus program pipeline

Write TI-BASIC → test it in a headless emulator that runs **your own calculator's ROM**
→ send it to the real calculator → run it there and read the real screen back over USB.
All from the command line, so an LLM can drive the whole loop on its own.

## For humans (quick start)

```bash
./ti84 test programs/trace            # run TRACE's tests in the emulator
./ti84 flash programs/trace/TRACE.bas # put it on the calculator
./ti84 hw run TRACE -i A              # run it on the calculator, print its screen
./ti84 hw screen out/now.png          # screenshot the calculator right now
```

Plug the calculator in with its USB cable and turn it on before any `flash` / `hw` command.
To get a new program, ask Claude: *"write a TI-84 program that …, test it, then put it on
my calculator"*. Claude should follow the workflow below. Nothing should reach the
calculator before it has passed its emulator tests.

Screenshots and test failures go to `out/`.

---

## For LLM agents

### The loop (follow this exactly)

1. **Write** `programs/<name>/<NAME>.bas`. The file name is the on-calc program name
   (1–8 chars, A–Z/0–9, starting with a letter). Syntax is the
   [tivars](https://github.com/TI-Toolkit/tivars_lib_py) text form (see *Source syntax*).
2. **Write tests** in `programs/<name>/test_*.py` (see *Test API*). Before writing code,
   cover the normal case, edge cases (1×1, negatives, decimals), invalid input, and any
   variables that already exist on the calculator.
3. **`./ti84 test programs/<name>`** builds every `.bas` in the folder, lints it, then
   runs each `test_*` function on a freshly booted emulator with the programs already
   loaded. On failure you get:
   - the OCR'd screen (8 lines × 16 chars),
   - `out/FAIL_<test>.png` (open it with your image-reading tool when the text isn't enough),
   - on an `ERR:` screen, the **Goto** view with `^` under the token that caused the error.
   Iterate until everything is green. `-k substr` runs a subset.
4. **`./ti84 run programs/<name>/<NAME>.bas -i INPUT -i INPUT2`** runs it once,
   ad hoc, and prints the screen. Use it for exploring and for checking how the OS
   behaves before you write an assertion.
5. **`./ti84 flash programs/<name>/<NAME>.bas`** sends it to the calculator (via `tilp`).
   Optionally confirm with `./ti84 hw get program NAME`: the bytes must equal the built `.8xp`.
6. **`./ti84 hw run NAME -i INPUT`** runs it on the real calculator with remote
   keypresses, then screenshots and OCRs the real LCD (`out/HW_<NAME>.png`).

**Honesty rule:** a successful *transfer* does not mean the program *works*. Only say
"works on the calculator" after step 6 shows the expected output, or after the user
confirms it. Never overwrite the user's variables (matrices, lists, programs) without
asking. Back them up first if a test on hardware needs them.

### Emulator test API (`harness/ti84emu.py`, class `TI84`)

Each test gets `calc`, a booted TI-84 Plus in a RAM-cleared state. Emulated time is
~100× faster than real time and only advances when you call something.

```python
from ti84emu import matrix_data, decode_matrix, tifloat_encode, T_MATRIX, T_REAL, T_LIST

def test_2x2(calc):
    calc.send_var(T_MATRIX, b"\x5c\x00", matrix_data([[1, 2], [3, 4]]))  # [A]
    screen = calc.run_program("TRACE", inputs=["A"])   # list of 8 strings
    assert calc.error() is None, screen
    assert screen[screen.index("TRACE:") + 1].strip() == "5", screen
```

| Call | Does |
|---|---|
| `run_program(name, inputs=[...], settle=5.0)` | QUIT → PRGM menu → run; types each input + ENTER; returns screen lines |
| `text()` | OCR the home screen → 8 strings (right-stripped) |
| `error()` | `"SYNTAX"`, `"UNDEFINED"`, … if an `ERR:` screen is up, else `None` |
| `goto_error()` | choose Goto → `(editor_lines, (row, col) of cursor)` |
| `press("ENTER")`, `keys("SECOND","MODE")`, `type("A+1")` | physical keypresses |
| `run(seconds)` | advance emulated time |
| `send_var(type, name, data)` / `recv_var(type, name)` | link transfer (raw var data) |
| `send_file(path.8xp)` | send every var in a file |
| `png(path)`, `pixels()`, `ascii()` | raw LCD access (96×64) |

Var names: real `b"A"`…`b"Z"`, `b"\x5b"`=θ; matrix `[A]`..`[J]` = `5C 00`..`5C 09`;
list `L₁`..`L₆` = `5D 00`..`5D 05`; `Str1`..`Str0` = `AA 00`..`AA 09`; program = ASCII name.
Data helpers: `tifloat_encode(x)` for a real, `matrix_data(rows)`,
`decode_real/decode_list/decode_matrix`.

`type()` / `inputs` characters: `A–Z 0–9 . , + - * / ^ ( ) { } [ ] " : ? θ` and space;
`~` = the negative sign (−), `→` = STO, `\n` = ENTER. Key names for `press` are in the
`K` dict (`SECOND, ALPHA, MODE, PRGM, APPS, MATH, CLEAR, ENTER, UP, DOWN, LEFT, RIGHT, K0..K9, …`).

OCR conventions: negative numbers read as `⁻2.25` (the TI negative glyph), the
cursor reads as `█`, and unknown glyphs read as `?`. Subscripts such as `L₆` don't OCR
(they come out as `Lᴇ`); fall back to the PNG.

### Hardware commands (`./ti84 hw …`, `harness/hw.py`)

| Command | Does |
|---|---|
| `hw ping` | connect + handshake |
| `hw screen [out.png]` | screenshot the real LCD, print OCR |
| `hw run NAME -i A -i 3 [--wait 3]` | QUIT, CLEAR, type `prgmNAME`, ENTER, type inputs; screenshot + OCR |
| `hw keys "TEXT"` | remote keypresses (same chars as above; `\n` = ENTER) |
| `hw send FILE.8xp\|FILE.bas` | send via our own DUSB code (alternative to `flash`) |
| `hw get real X` / `hw get program NAME` | read a variable back |
| `hw -v …` | log every USB packet |

From Python: `from hw import Calc` → `with Calc() as c: c.key(code); c.type(s); c.text();
c.screenshot(); c.send_var(...); c.recv_var(...); c.run_program(name, inputs)`.
For OS keycodes not in `hw.KEYCODE` (e.g. the MATRIX menu = `0x37`, QUIT `0x40`,
CLEAR `0x09`, ENTER `0x05`, the `prgm` token `0xDA`), call `c.key(code)` directly. Example:
storing `[[5,7][2,3]]→[A]` on the calculator was
`c.type("[[5,7][2,3]]→"); c.key(0x37); c.key(0x05); c.key(0x05)`.

The text reader handles the real LCD's vertical scroll offset automatically.

### Source syntax and TI-BASIC gotchas

These each caused real failures. The linter (`harness/tibasic.py`) catches the first one.

- **Commands keep their trailing space** in tivars syntax: `Disp `, `Pause `, `Input `,
  `Prompt `, `If `, `Output(`… Writing `Pause` without the space silently becomes the letters
  `P a u s e` and gives ERR:SYNTAX. The lint rejects lowercase-letter tokens outside strings.
- `→` or `->` = STO. `≠ ≤ ≥`, `L₁`, `[A]`, `Str1`, `θ` are written literally. `:` separates
  statements on one line (`If N=1:Then:…:End`).
- **You can't build names from strings.** `expr("["+Str1+"]")` produces the bracket *character*
  tokens, not the `[A]` matrix token, so it throws ERR:SYNTAX (this was the original TRACE bug).
  Branch with `If` instead.
- `(row,col)` indexing works only on a real matrix token (`[A](I,J)`), not on `Ans` or `expr(…)`.
- `→` inside a string literal ends the string; `"` can't appear inside a string.
- A Disp/Input line of exactly 16 chars wraps and leaves an empty line under it. Find
  results by searching for a label (`screen.index("TRACE:")`), not by fixed row numbers.
- TI-BASIC has no error trapping. If a test expects an error, assert `calc.error() == "…"`.
- Variables a program uses (`N`, `I`, `Str1`, `L₆`, …) are global and persist on the
  user's calculator. Prefer variables the program already owns.

### Layout

```
ti84                     CLI (runs with venv/bin/python)
programs/<name>/         <NAME>.bas + test_*.py  (built .8xp lands here, gitignored)
harness/
  tihl.c, config.h       C shim exposing the TilEm core (keys, link port, LCD) to Python
  build.sh → libtihl.so  compiles vendor/tilem-2.0/emu/*.c + tihl.c
  ti84emu.py             emulator driver + DBUS link protocol + TI float/matrix codecs
  ocr.py, font.json      home-screen OCR; font calibrated from the emulator itself
  tibasic.py             tokenize (tivars) + lint
  hw.py                  real calculator over USB (DUSB): send/get/keys/screenshot/run
  romdump.py             DUSB transport + ROM dumper client
  ROMDUMP_84p.8xp        on-calc ROM dumper (from tilibs)
vendor/tilem-2.0/emu     TilEm 2.0 emulation core (LGPL)
ti84p_dump.rom           the user's ROM: gitignored, never commit or share
out/                     screenshots, failure artefacts
```

---

## Installation (fresh machine)

Requirements: Linux, gcc, Python 3.10+, a TI-84 Plus (non-SE/non-CE; others untested),
and a USB mini-B cable.

```bash
sudo apt install build-essential python3-venv tilp2      # tilp2 pulls in libticables + udev rule
python3 -m venv venv && venv/bin/pip install -r requirements.txt
harness/build.sh                                         # builds harness/libtihl.so
```

The `libticables2` package installs `/usr/lib/udev/rules.d/69-libticables2-*.rules`,
which gives your user access to the calculator (`0451:e003`). If `./ti84 hw ping` says
"Access denied", add `SUBSYSTEM=="usb", ATTR{idVendor}=="0451", TAG+="uaccess"` to a file in
`/etc/udev/rules.d/`, then `sudo udevadm control --reload` and replug.

### Getting the ROM (one time)

TI doesn't distribute the OS ROM, so dump it from your own calculator. `tilp`'s built-in
ROM dump fails on this setup with ERR_INVALID_PACKET, so use the bundled client:

```bash
tilp --no-gui --silent harness/ROMDUMP_84p.8xp   # put the dumper program on the calculator
venv/bin/python harness/romdump.py ti84p_dump.rom   # ~100 s, 1 MiB
```

Check: the file is 1,048,576 bytes and contains the string `TI-84 Plus`. Then rebuild
the OCR font so it matches your OS version:

```bash
venv/bin/python harness/ocr.py
./ti84 test programs/trace          # should be all PASS
```

## Troubleshooting

- **Test sees the wrong screen or a dropped key:** right after a menu selection the OS
  ignores keys for ~0.25 s of emulated time. `press()` already waits 0.6 s; add
  `calc.run(1)` before reading the screen if a program does heavy work.
- **`program X not visible in PRGM menu`:** `run_program` only finds programs on the
  first page of the menu. Keep tests to a few programs each.
- **`hw` error `0x000e` on a matrix:** sending or reading matrices over DUSB doesn't
  work yet (the name encoding for matrix vars is wrong). Reals, programs and screenshots
  work. To set a matrix on hardware, type it with remote keys (see the example above).
- **`calculator error` right after another tool used the link:** unplug and replug,
  or press ON on the calculator, then retry.
- **Slow tests:** they normally take ~0.25 s each. If OCR shows many `?`, `read_screen`
  searches pixel offsets, which costs more. Check `out/*.png` for glyphs the font lacks.
