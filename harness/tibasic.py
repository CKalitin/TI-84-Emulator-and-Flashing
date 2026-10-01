"""TI-BASIC source -> tokenized program, with lint checks that catch the
silent mis-tokenization problems tivars lets through.

Source syntax is tivars' (e.g. `->` or `→` for store, `Disp `, `If `, `Pause `
keep their trailing space; `L₁`, `[A]`, `Str1`, `≠`, `≤` ...).
"""
import os

from tivars.models import TI_84P
from tivars.types import TIProgram

TWO_BYTE_PREFIXES = {0x5C, 0x5D, 0x5E, 0x60, 0x61, 0x62, 0x63, 0x7E, 0xAA, 0xBB, 0xEF}
QUOTE, NEWLINE, STORE = 0x2A, 0x3F, 0x04


class LintError(Exception):
    pass


def iter_tokens(data):
    """Yield (offset, token_bytes)."""
    i = 0
    while i < len(data):
        n = 2 if data[i] in TWO_BYTE_PREFIXES and i + 1 < len(data) else 1
        yield i, data[i:i + n]
        i += n


def lint(data, source):
    """Return a list of problems found in tokenized program `data`."""
    problems = []
    in_str = False
    line = 1
    lines = source.split("\n")
    for _, tok in iter_tokens(data):
        b = tok[0]
        if b == NEWLINE:
            line, in_str = line + 1, False
            continue
        if b == STORE:
            in_str = False
            continue
        if b == QUOTE:
            in_str = not in_str
            continue
        # Lowercase letters (BB B0..BB CE) outside a string literal are almost
        # always a command tivars failed to recognise, e.g. "Pause" (needs
        # "Pause "), "Disp" without its space, or a typo'd command name.
        if not in_str and len(tok) == 2 and tok[0] == 0xBB and 0xB0 <= tok[1] <= 0xCE:
            src = lines[line - 1] if line - 1 < len(lines) else ""
            problems.append("line %d: lowercase letter token outside a string -> "
                            "probably a mis-tokenized command: %r" % (line, src))
    seen, out = set(), []  # one report per line
    for p in problems:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def compile_source(source, name):
    """Tokenize `source` into a TIProgram named `name`; raises LintError."""
    name = name.upper()
    if not (1 <= len(name) <= 8 and name[0].isalpha() and name.isalnum()):
        raise LintError("bad program name %r (1-8 chars, A-Z/0-9, starts with letter)" % name)
    source = source.replace("\r\n", "\n").strip("\n")
    prog = TIProgram(name=name)
    prog.load_string(source, model=TI_84P)
    problems = lint(bytes(prog.data), source)
    if problems:
        raise LintError("\n".join(problems))
    return prog


def compile_file(path, out_dir=None):
    """Compile NAME.bas -> NAME.8xp next to it (or in out_dir). Returns 8xp path."""
    name = os.path.splitext(os.path.basename(path))[0]
    with open(path, encoding="utf-8") as f:
        prog = compile_source(f.read(), name)
    out = os.path.join(out_dir or os.path.dirname(os.path.abspath(path)), name.upper() + ".8xp")
    prog.save(out)
    return out


def decompile(path):
    return TIProgram.open(path).string(model=TI_84P)
