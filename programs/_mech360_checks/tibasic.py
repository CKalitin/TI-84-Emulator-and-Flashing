"""Tiny TI-BASIC interpreter for the subset used by the MECH 360 programs.

Executes the actual .txt sources (TI-84 display form: → ≤ ≥ ≠ ² ³ √( ⁻ π θ L₁ ᴇ).
Strict on purpose: implicit multiplication and unclosed parentheses are rejected,
so the sources are unambiguous on the real calculator too.

run(path_or_src, inputs) -> Result(outputs={label: [values]}, messages=[...], transcript=[...])
  inputs: list of numbers consumed in order by Prompt / Input / Menu (Menu: 1-based choice).
"""
import math, re

FUNCS = {
    'sin(': 1, 'cos(': 1, 'tan(': 1, 'sin⁻¹(': 1, 'cos⁻¹(': 1, 'tan⁻¹(': 1,
    '√(': 1, 'abs(': 1, 'max(': 2, 'min(': 2, 'int(': 1, 'iPart(': 1, 'fPart(': 1,
    'round(': 2, 'ln(': 1, 'log(': 1, 'R►Pθ(': 2, 'R►Pr(': 2, 'dim(': 1, 'not(': 1,
}
FUNC_NAMES = sorted(FUNCS, key=len, reverse=True)
LISTS = ['L₁', 'L₂', 'L₃', 'L₄', 'L₅', 'L₆']


class TIError(Exception):
    pass


def tokenize(s):
    toks, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch == ' ':
            raise TIError(f'stray space in expression: {s!r}')
        if ch == '"':
            j = s.find('"', i + 1)
            j = len(s) if j < 0 else j
            toks.append(('str', s[i + 1:j])); i = j + 1; continue
        m = re.match(r'(\d+\.?\d*|\.\d+)(ᴇ⁻?\d+)?', s[i:])
        if m:
            txt = m.group(0).replace('ᴇ', 'e').replace('⁻', '-')
            toks.append(('num', float(txt))); i += len(m.group(0)); continue
        f = next((f for f in FUNC_NAMES if s.startswith(f, i)), None)
        if f:
            toks.append(('func', f)); i += len(f); continue
        l = next((l for l in LISTS if s.startswith(l, i)), None)
        if l:
            toks.append(('list', l)); i += len(l); continue
        if ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZθ':
            toks.append(('var', ch)); i += 1; continue
        if ch == 'π':
            toks.append(('num', math.pi)); i += 1; continue
        for op in ('and', 'or', 'xor'):
            if s.startswith(op, i):
                toks.append(('op', op)); i += len(op); break
        else:
            if ch in '+-*/^=≠<>≤≥(),⁻²³→':
                toks.append(('op', ch)); i += 1; continue
            raise TIError(f'bad char {ch!r} in {s!r}')
    return toks


class Parser:
    # binding powers (TI-84): or/xor 10, and 20, relational 30, +- 40, */ 50,
    # negation 60 (prefix), ^ 70, postfix ²³ 80
    BIN = {'or': 10, 'xor': 10, 'and': 20, '=': 30, '≠': 30, '<': 30, '>': 30, '≤': 30, '≥': 30,
           '+': 40, '-': 40, '*': 50, '/': 50, '^': 70}

    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self):
        tok = self.peek(); self.i += 1; return tok

    def expect(self, v):
        tok = self.take()
        if tok != ('op', v):
            raise TIError(f'expected {v!r}, got {tok}')

    def parse(self, rbp=0):
        left = self.nud()
        while True:
            kind, v = self.peek()
            if kind == 'op' and v in ('²', '³'):
                self.take(); left = ('pow', left, ('num', 2.0 if v == '²' else 3.0)); continue
            if kind == 'op' and v in self.BIN and self.BIN[v] > rbp:
                self.take()
                rb = self.BIN[v] - 1 if v == '^' and False else self.BIN[v]  # ^ is left-assoc on TI
                right = self.parse(rb)
                left = ('bin', v, left, right); continue
            if kind in ('num', 'var', 'func', 'list', 'str') or (kind == 'op' and v in ('(', '⁻')):
                raise TIError('implicit multiplication not allowed (write *)')
            return left

    def nud(self):
        kind, v = self.take()
        if kind == 'num':
            return ('num', v)
        if kind == 'str':
            return ('str', v)
        if kind == 'var':
            return ('var', v)
        if kind == 'list':
            if self.peek() == ('op', '('):
                self.take(); idx = self.parse(); self.expect(')')
                return ('lidx', v, idx)
            return ('list', v)
        if kind == 'op' and v == '(':
            e = self.parse(); self.expect(')'); return e
        if kind == 'op' and v == '⁻':
            return ('neg', self.parse(60))
        if kind == 'func':
            args = [self.parse()]
            while self.peek() == ('op', ','):
                self.take(); args.append(self.parse())
            self.expect(')')
            if len(args) != FUNCS[v]:
                raise TIError(f'{v} wants {FUNCS[v]} args')
            return ('call', v, args)
        if kind == 'op' and v == '-':
            raise TIError('binary minus "-" used as negation; use ⁻')
        raise TIError(f'unexpected token {kind} {v}')


def parse_expr(s):
    p = Parser(tokenize(s))
    e = p.parse()
    if p.i != len(p.t):
        raise TIError(f'trailing tokens in {s!r}: {p.t[p.i:]}')
    return e


def split_args(s):
    """Split top-level commas (outside strings/parens)."""
    out, depth, cur, ins = [], 0, '', False
    for ch in s:
        if ch == '"':
            ins = not ins
        if not ins and ch == '(':
            depth += 1
        if not ins and ch == ')':
            depth -= 1
        if not ins and depth == 0 and ch == ',':
            out.append(cur); cur = ''
        else:
            cur += ch
    out.append(cur)
    return out


def split_statements(src):
    stmts = []
    for line in src.split('\n'):
        cur, ins = '', False
        for ch in line:
            if ch == '"':
                ins = not ins
            if ch == ':' and not ins:
                stmts.append(cur); cur = ''
            else:
                cur += ch
        stmts.append(cur)
    return [s for s in stmts if s.strip() != '']


class Result:
    def __init__(self):
        self.outputs, self.messages, self.transcript = {}, [], []

    def get(self, label, idx=-1):
        return self.outputs[label][idx]


class Machine:
    def __init__(self, src):
        self.stmts = split_statements(src)
        self.labels = {}
        for i, s in enumerate(self.stmts):
            if s.startswith('Lbl '):
                self.labels[s[4:]] = i
        self.cache = {}

    def ev(self, s):
        if s not in self.cache:
            self.cache[s] = parse_expr(s)
        return self.e(self.cache[s])

    def trig_in(self, x):
        return x if self.radian else x * math.pi / 180

    def trig_out(self, x):
        return x if self.radian else x * 180 / math.pi

    def e(self, n):
        k = n[0]
        if k == 'num':
            return n[1]
        if k == 'str':
            return n[1]
        if k == 'var':
            if n[1] not in self.vars:
                raise TIError(f'variable {n[1]} read before set (calculator would use a stale value)')
            return self.vars[n[1]]
        if k == 'lidx':
            L = self.lists[n[1]]; i = int(self.e(n[2]))
            if not 1 <= i <= len(L):
                raise TIError('ERR:INVALID DIM')
            return L[i - 1]
        if k == 'neg':
            return -self.e(n[1])
        if k == 'pow':
            return self.e(n[1]) ** self.e(n[2])
        if k == 'bin':
            op, a, b = n[1], self.e(n[2]), self.e(n[3])
            if op == '+': return a + b
            if op == '-': return a - b
            if op == '*': return a * b
            if op == '/':
                if b == 0: raise TIError('ERR:DIVIDE BY 0')
                return a / b
            if op == '^':
                if a < 0 and b != int(b): raise TIError('ERR:NONREAL ANS')
                return a ** b
            return float({'=': a == b, '≠': a != b, '<': a < b, '>': a > b, '≤': a <= b, '≥': a >= b,
                          'and': bool(a) and bool(b), 'or': bool(a) or bool(b), 'xor': bool(a) != bool(b)}[op])
        if k == 'call':
            f = n[1]
            if f == 'dim(':
                return float(len(self.lists[n[2][0][1]]))
            a = [self.e(x) for x in n[2]]
            if f == 'sin(': return math.sin(self.trig_in(a[0]))
            if f == 'cos(': return math.cos(self.trig_in(a[0]))
            if f == 'tan(': return math.tan(self.trig_in(a[0]))
            if f == 'sin⁻¹(': return self.trig_out(math.asin(a[0]))
            if f == 'cos⁻¹(': return self.trig_out(math.acos(a[0]))
            if f == 'tan⁻¹(': return self.trig_out(math.atan(a[0]))
            if f == '√(':
                if a[0] < 0: raise TIError('ERR:NONREAL ANS')
                return math.sqrt(a[0])
            if f == 'abs(': return abs(a[0])
            if f == 'max(': return max(a)
            if f == 'min(': return min(a)
            if f == 'int(': return float(math.floor(a[0]))
            if f == 'iPart(': return float(int(a[0]))
            if f == 'fPart(': return a[0] - int(a[0])
            if f == 'round(': return round(a[0], int(a[1]))
            if f == 'ln(': return math.log(a[0])
            if f == 'log(': return math.log10(a[0])
            if f == 'R►Pθ(':
                if a[0] == 0 and a[1] == 0: return 0.0
                return self.trig_out(math.atan2(a[1], a[0]))
            if f == 'R►Pr(': return math.hypot(a[0], a[1])
            if f == 'not(': return float(not a[0])
        raise TIError(f'cannot eval {n}')

    def find_block_end(self, i, stop_at_else):
        """From statement after i, find matching End (or Else at depth 0)."""
        depth, j = 0, i + 1
        while j < len(self.stmts):
            s = self.stmts[j]
            if s == 'Then' or s.startswith('For(') or s.startswith('While ') or s.startswith('Repeat '):
                depth += 1
            elif s == 'End':
                if depth == 0:
                    return j
                depth -= 1
            elif s == 'Else' and depth == 0 and stop_at_else:
                return j
            j += 1
        raise TIError(f'no End for statement {i}: {self.stmts[i]}')

    def store(self, target, val):
        if re.fullmatch(r'[A-Zθ]', target):
            self.vars[target] = val; return
        m = re.fullmatch(r'(L[₁-₆])\((.+)\)', target)
        if m:
            L = self.lists.setdefault(m.group(1), []); i = int(self.ev(m.group(2)))
            if i == len(L) + 1: L.append(val)
            elif 1 <= i <= len(L): L[i - 1] = val
            else: raise TIError('ERR:INVALID DIM')
            return
        m = re.fullmatch(r'dim\((L[₁-₆])\)', target)
        if m:
            L = self.lists.setdefault(m.group(1), []); n = int(val)
            del L[n:]; L.extend([0.0] * (n - len(L))); return
        raise TIError(f'bad store target {target}')

    def run(self, inputs, max_steps=200000):
        self.vars, self.lists, self.radian = {}, {}, True
        res, inp, stack, pc, steps = Result(), list(inputs), [], 0, 0

        def pop_input(prompt):
            if not inp:
                raise TIError(f'out of inputs at prompt {prompt!r}')
            v = inp.pop(0); res.transcript.append(f'{prompt}{v}'); return float(v)

        while pc < len(self.stmts):
            steps += 1
            if steps > max_steps:
                raise TIError('step limit (infinite loop?)')
            s = self.stmts[pc]
            nxt = pc + 1
            if s in ('Radian', 'Degree'):
                self.radian = s == 'Radian'
            elif s in ('ClrHome', 'Pause'):
                pass
            elif s in ('Stop', 'Return'):
                break
            elif s.startswith('Lbl '):
                pass
            elif s.startswith('Goto '):
                nxt = self.labels[s[5:]]
            elif s.startswith('Disp '):
                items = split_args(s[5:]); pending = None
                for it in items:
                    if it.startswith('"'):
                        txt = it.strip('"'); res.transcript.append(txt)
                        if pending is not None: res.messages.append(pending)
                        pending = txt
                    else:
                        v = self.ev(it); res.transcript.append(f'   {v:.10g}')
                        res.outputs.setdefault(pending if pending is not None else it, []).append(v)
                        pending = None
                if pending is not None: res.messages.append(pending)
            elif s.startswith('Prompt '):
                for v in s[7:].split(','):
                    self.store(v, pop_input(v + '=?'))
            elif s.startswith('Input '):
                a = split_args(s[6:])
                self.store(a[1], pop_input(a[0].strip('"')))
            elif s.startswith('Menu('):
                a = split_args(s[5:-1] if s.endswith(')') else s[5:])
                title = a[0].strip('"'); items = a[1:]
                choice = int(pop_input(f'MENU {title} #'))
                nxt = self.labels[items[2 * (choice - 1) + 1]]
            elif s.startswith('If '):
                c = self.ev(s[3:])
                then = pc + 1 < len(self.stmts) and self.stmts[pc + 1] == 'Then'
                if then:
                    if c:
                        stack.append(('if',)); nxt = pc + 2
                    else:
                        j = self.find_block_end(pc + 1, True)
                        if self.stmts[j] == 'Else':
                            stack.append(('if',))
                        nxt = j + 1
                else:
                    nxt = pc + 1 if c else pc + 2
            elif s == 'Else':
                j = self.find_block_end(pc, False)
                stack.pop(); nxt = j + 1
            elif s.startswith('For('):
                a = split_args(s[4:-1] if s.endswith(')') else s[4:])
                var, lo, hi = a[0], self.ev(a[1]), self.ev(a[2])
                step = self.ev(a[3]) if len(a) > 3 else 1.0
                self.vars[var] = lo
                if (step > 0 and lo > hi) or (step < 0 and lo < hi):
                    nxt = self.find_block_end(pc, False) + 1
                else:
                    stack.append(('for', pc, var, a[2], step))
            elif s.startswith('While '):
                if self.ev(s[6:]):
                    stack.append(('while', pc))
                else:
                    nxt = self.find_block_end(pc, False) + 1
            elif s == 'End':
                if not stack:
                    raise TIError(f'End without block at {pc}')
                fr = stack[-1]
                if fr[0] == 'if':
                    stack.pop()
                elif fr[0] == 'for':
                    _, fpc, var, hi, step = fr
                    self.vars[var] += step
                    h = self.ev(hi)
                    if (step > 0 and self.vars[var] <= h) or (step < 0 and self.vars[var] >= h):
                        nxt = fpc + 1
                    else:
                        stack.pop()
                elif fr[0] == 'while':
                    stack.pop(); nxt = fr[1]
            elif s == 'Then':
                raise TIError(f'Then without If at {pc}')
            elif '→' in s:
                expr, target = s.rsplit('→', 1)
                self.store(target, self.ev(expr))
            else:
                self.ev(s)  # bare expression (sets Ans on calc)
            pc = nxt
        if inp:
            raise TIError(f'unused inputs: {inp}')
        return res


def run(src_or_path, inputs):
    src = open(src_or_path, encoding='utf-8').read() if src_or_path.endswith('.txt') else src_or_path
    return Machine(src).run(inputs)
