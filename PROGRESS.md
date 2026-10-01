# Progress

## Status (2026-09-30)

| Piece | State |
|---|---|
| Headless emulator (TilEm core + user's ROM, no GUI/X11) | **done**, boots in ~30 ms |
| Link: send/receive vars to emulator (DBUS) | **done**, round-trip verified |
| Keypad input, LCD capture, PNG, OCR (calibrated from emulator) | **done** |
| ERR detection + Goto with exact error position | **done** |
| Tokenizer lint (catches silent mis-tokenization) | **done** |
| Test runner `./ti84 test` | **done** |
| TRACE program | **fixed and verified on the real calculator**: `[[5,7][2,3]]→[A]` typed remotely, TRACE printed 8 |
| Flash to calculator (`./ti84 flash`, via tilp) | **done**, TRACE read back byte-identical |
| Hardware: screenshot+OCR, remote keys, run, get real/program (`./ti84 hw`) | **done, verified on the calculator** |
| Hardware: matrix send/get over DUSB | broken (error 0x000e) — open |

See README.md for how to use the pipeline.

## TRACE root cause (confirmed in emulator)

`expr("["+Str1+"]")`: `"["` inside a string is the bracket character token (0x06),
not part of the 2-byte matrix-name token `[A]` (5C 00). `expr` therefore parses
`[ A ]` as a malformed matrix literal → ERR:SYNTAX. The emulator reproduces the exact
ERR:SYNTAX the calculator showed. TI-BASIC cannot build a matrix name from a string,
so the new version branches on `inString("ABCDEFGHIJ",Str1)` and computes the trace
with `sum(seq([X](I,I),I,1,min(dim([X]))))`, touching no other matrix.

(Earlier attempts' theories — Ans subscripting, unterminated strings — were not the cause.)

## History

- Packaged tilp's ROM dump fails (ERR_INVALID_PACKET, 5 times). A from-scratch DUSB
  client (`harness/romdump.py`) dumped the ROM successfully → `ti84p_dump.rom`.
- TilEm GUI + Xvfb + xdotool clicking was fragile (dropped chords, blank screen without
  skin). Replaced by linking TilEm's C emulation core directly (`harness/tihl.c`).
