"""Run every worked example two ways:
  TI  = the actual <NAME>.txt TI-BASIC source executed by tibasic.py (inputs fed in prompt order)
  REF = reference.py (Python transliteration)
Pass if both are within TOL (0.5 %) of the expected value from the course source.
Usage: python3 tests.py [PROGRAM ...]"""
import os, sys, math
import numpy as np
import tibasic, reference as R

HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 0.005
CASES = []  # (prog, case, ti_inputs, ref_fn, checks[(label, idx, expected, source)], messages)


def case(prog, name, ti, ref, checks, msgs=()):
    CASES.append((prog, name, ti, ref, checks, msgs))


# ---------------- PLAST ----------------
case('PLAST', 'MT2-25 Q3 rect', [1, 50, 120, 200e3, 220, 1, 40],
     lambda: R.PLAST(1, 50, 120, 200e3, 220, 1, 40),
     [('M=', 0, 33.73e6, 'MT2 sol: 33.73 kN·m (N·mm)'), ('SIG UNLOAD(C)=', 0, 281.1, 'MT2 sol'),
      ('SRES(C)=', 0, 61.11, 'MT2 sol'), ('SRES(YY)=', 0, -32.59, 'MT2 sol'),
      ('RHO RESID=', 0, 245.5e3, 'MT2 sol: 245.5 m (mm)'), ('K=ZX/SX', 0, 1.5, 'rect k=1.5')])
case('PLAST', 'Lec16 flanged I', [2, 8, .5, .5, 10, 29000, 36, 2, 1650],
     lambda: R.PLAST(2, 8, .5, .5, 10, 29000, 36, 2, 1650),
     [('IX=', 0, 211.04, 'Lec16'), ('K=ZX/SX', 0, 1.1402, 'Lec16'), ('MY=', 0, 1519.5, 'Lec16'),
      ('MP=', 0, 1732.5, 'Lec16'), ('YY=', 0, 3.708, 'Lec16'), ('SIG UNLOAD(C)=', 0, 39.1, 'Lec16'),
      ('SRES(C)=', 0, 3.09, 'Lec16'), ('SRES(YY)=', 0, -7.01, 'Lec16 (7.01, opposite sign)'),
      ('SRES=0 AT Y=', 0, 4.608, 'Lec16 (src rounding; exact 4.6045)'),
      ('RHO RESID=', 0, 1278.6 * 12, 'Lec16: 1278.6 ft (in)')])
case('PLAST', 'LecX2 2.4 box, core=b', [3, 18, 18, 3, 20000, 25, 1, 6],
     lambda: R.PLAST(3, 18, 18, 3, 20000, 25, 1, 6),
     [('M=', 0, 23850, 'LecX2: 238.5 kN·m (kN·cm, SY=25 kN/cm²)')])
case('PLAST', 'LecX2 2.4 box, M=250', [3, 18, 18, 3, 20000, 25, 2, 25000],
     lambda: R.PLAST(3, 18, 18, 3, 20000, 25, 2, 25000), [('YY=', 0, 3.606, 'LecX2')])
case('PLAST', 'LecX2 2.4 box, M=220', [3, 18, 18, 3, 20000, 25, 2, 22000],
     lambda: R.PLAST(3, 18, 18, 3, 20000, 25, 2, 22000), [('YY=', 0, 7.666, 'LecX2')], ['(YY IN FLANGE)'])
case('PLAST', 'guard: M<MY', [1, 50, 120, 200e3, 220, 2, 1e6], None, [], ['M≤MY ELASTIC'])
case('PLAST', 'round trip yY->M->yY', [2, 8, .5, .5, 10, 29000, 36, 2, R.PLAST(2, 8, .5, .5, 10, 29000, 36, 1, 4.2)['M=']],
     None, [('YY=', 0, 4.2, 'self-consistency')], ['(YY IN WEB)'])

# ---------------- SCENT ----------------
mt = [(0, 1, .5, 2, 4), (4, 3, 0, 4, 6), (4, -3, .5, 2, 4)]
case('SCENT', 'MT2-25 Q1 (k=1)', [1, 3] + sum([list(s) for s in mt], []), lambda: R.SCENT(1, mt),
     [('F/V=', 0, 10 / 3, 'spec'), ('F/V=', 1, 40, 'MT2 sol F_BC=40/k'), ('F/V=', 2, 10 / 3, 'spec'),
      ('E=SUM(R*F/V)', 0, 266.667, 'MT2 sol 266.667/k')])
ui = [(0, 3, 0, 3.25, 6), (0, 3, 0, 1.75, -6)]
case('SCENT', 'LecX2 2.2 unsym I', [108, 2] + sum([list(s) for s in ui], []), lambda: R.SCENT(108, ui),
     [('F/V=', 0, 15.844 / 108, 'LecX2'), ('F/V=', 1, 4.594 / 108, 'LecX2'), ('E=SUM(R*F/V)', 0, 0.625, 'LecX2')])
pu = [(54, 6, 0, 4, 12), (78, 6, -.5, 12, 4)]
case('SCENT', 'LecX2 2.3 pulse', [1440, 2] + sum([list(s) for s in pu], []), lambda: R.SCENT(1440, pu),
     [('F/V=', 0, 264 / 1440, 'LecX2'), ('F/V=', 1, 1080 / 1440, 'LecX2'), ('E=SUM(R*F/V)', 0, 5.2, 'LecX2')])

# ---------------- EULER ----------------
Isq = .5**4 / 12
case('EULER', 'MT2-25 Q2 AB', [1, 29000, .25, Isq, 5, 3, 1, 0, 0],
     lambda: R.EULER(29000, .25, Isq, 0, 5, 3, 0, 1, 0, 0),
     [('RGYR=', 0, .1443, 'MT2'), ('LAMBDA=KL/R', 0, 34.64, 'MT2'), ('PCR=', 0, 59.63, 'MT2')])
case('EULER', 'MT2-25 Q2 CE (via RGYR)', [1, 29000, .25, 0, sqrt := math.sqrt(Isq / .25), 10, 3, 1, 0, 0],
     lambda: R.EULER(29000, .25, 0, sqrt, 10, 3, 0, 1, 0, 0),
     [('LAMBDA=KL/R', 0, 69.28, 'MT2'), ('PCR=', 0, 14.91, 'MT2')])
case('EULER', 'MT2-25 Q2(d) ratio', [2, 1, .7], lambda: R.EULER_RATIO(1, .7), [('PCR NEW/OLD=', 0, 2.04, 'MT2')])
case('EULER', 'Lec13 W8x24 weak n=2', [1, 29000, 7.08, 18.3, 420, 3, 2, 36, 0],
     lambda: R.EULER(29000, 7.08, 18.3, 0, 420, 3, 0, 2, 36, 0),
     [('LAMBDA=KL/R', 0, 261.24, 'Lec13'), ('SIGCR=', 0, 16.776, 'Lec13'), ('PCR=', 0, 118.771, 'Lec13')])
case('EULER', 'Lec13 W8x24 strong n=1', [1, 29000, 7.08, 82.8, 420, 3, 1, 36, 118.771 / 2.5],
     lambda: R.EULER(29000, 7.08, 82.8, 0, 420, 3, 0, 1, 36, 118.771 / 2.5),
     [('RGYR=', 0, 3.420, 'Lec13'), ('LAMBDA=KL/R', 0, 122.82, 'Lec13'), ('SIGCR=', 0, 18.976, 'Lec13'),
      ('PCR=', 0, 134.35, 'Lec13'), ('LAMBDA CROSS=', 0, math.pi / math.sqrt(36 / 29000), 'formula'),
      ('FS BUCK=PCR/P', 0, 134.35 / (118.771 / 2.5), 'formula')])
case('EULER', 'stocky column yields first', [1, 29000, .25, Isq, 1, 3, 1, 36, 0], None, [], ['YIELDS FIRST'])
case('EULER', 'fixed-pin menu item K=.699', [1, 200e3, 100, 1000, 1000, 2, 1, 0, 0],
     None, [('PCR=', 0, math.pi**2 * 200e3 * 1000 / (0.699155 * 1000)**2, 'formula')])

# ---------------- SECT ----------------
def sect_inputs(rects):
    return [len(rects)] + sum([list(r) for r in rects], [])
for nm, rects, chk in [
    ('LecX2 2.1 H-beam (cm)', [(2, 18, -7, 0), (2, 18, 7, 0), (12, 2, 0, 4), (12, 2, 0, -4)],
     [('A=', 0, 120, 'LecX2'), ('IX=', 0, 2728, 'LecX2'), ('IY=', 0, 4128, 'LecX2')]),
    ('Lec15/16 flanged I (in)', [(8, .5, 0, 4.75), (.5, 9, 0, 0), (8, .5, 0, -4.75)],
     [('IX=', 0, 211.04, 'Lec16'), ('IY=', 0, 42.760, 'Lec16')]),
    ('Lec06 ex1 L-shape (mm)', [(10, 80, 0, 35), (50, 10, 30, 0)],
     [('XBAR=', 0, 11.54, 'Lec06'), ('YBAR=', 0, 21.54, 'Lec06'), ('IX=', 0, 8.0776e5, 'Lec06'),
      ('IY=', 0, 3.8776e5, 'Lec06'), ('IXY=-INT(XY)DA', 0, 3.2308e5, 'Lec06'),
      ('IU=C+R (MAX)', 0, 9.8309e5, 'Lec06 Istrong'), ('IV=C-R (MIN)', 0, 2.1243e5, 'Lec06 Iweak'),
      ('TO IU AXIS', 0, 28.49, 'Lec06: strong 28.49° CCW from x')]),
    ('Lec06 ex2 Z-shape (mm)', [(10, 40, -40, 25), (90, 10, 0, 0), (10, 40, 40, -25)],
     [('IX=', 0, 6.142e5, 'Lec06'), ('IY=', 0, 1.8942e6, 'Lec06'), ('IXY=-INT(XY)DA', 0, 8e5, 'Lec06'),
      ('IU=C+R (MAX)', 0, 2.2787e6, 'Lec06'), ('IV=C-R (MIN)', 0, 0.2297e6, 'Lec06'),
      ('TO IU AXIS', 0, 90 - 25.67, 'Lec06: strong 25.67° CW of y')]),
    ('hollow square hole', [(10, 10, 0, 0), (-4, 4, 0, 0)],
     [('A=', 0, 84, 'hand'), ('IX=', 0, (10**4 - 4**4) / 12, 'hand'), ('IY=', 0, (10**4 - 4**4) / 12, 'hand')]),
]:
    case('SECT', nm, sect_inputs(rects), (lambda r=rects: R.SECT(r)), chk)

# ---------------- SHEAR ----------------
case('SHEAR', 'LecX2 2.1(1) V-y=8kN', [1, 8, 2728, 1, 12, 4, 2], lambda: R.SHEAR_Q(8, 2728, [(12, 4)], 2),
     [('Q=SUM(A*Y)', 0, 48, 'LecX2'), ('SHEAR FLOW q=', 0, 0.141, 'LecX2 kN/cm'),
      ('TAU AV=q/T', 0, 0.0703, 'LecX2 0.703 MPa = 0.0703 kN/cm²')])
case('SHEAR', 'LecX2 2.1(2) Vx=15kN', [1, 15, 4128, 1, 18, 7, 2], lambda: R.SHEAR_Q(15, 4128, [(18, 7)], 2),
     [('Q=SUM(A*Y)', 0, 126, 'LecX2'), ('SHEAR FLOW q=', 0, 0.4578, 'LecX2 prints 0.229 (typo; = tau in kN/cm²)'),
      ('TAU AV=q/T', 0, 0.2289, 'LecX2 2.289 MPa')])
case('SHEAR', 'LecX2 2.1(3) V=20kN 55deg', [3, -16.383, 11.472, 48, 2728, 126, 4128, 2],
     lambda: R.SHEAR_2(-16.383, 11.472, 48, 2728, 126, 4128, 2),
     [('q REINFORCE=', 0, 0.638, 'LecX2'), ('TAU REINF=', 0, 0.3192, 'LecX2 3.192 MPa')])
case('SHEAR', 'Lec11 4.3 nailed T', [2, 101.25, 1, 300, 0], lambda: R.SHEAR_FAST(101.25, 0, 0, 0, 1, 300, 0),
     [('MAX SPACING=', 0, 2.96, 'Lec11')])
case('SHEAR', 'fastener force via V,Q,I', [2, 0, 10, 48, 2728, 2, 0, 5], lambda: R.SHEAR_FAST(0, 10, 48, 2728, 2, 0, 5),
     [('q=', 0, 10 * 48 / 2728, 'formula'), ('F PER FASTENER=', 0, 10 * 48 / 2728 * 5 / 2, 'formula')])

# ---------------- SECANT ----------------
case('SECANT', 'Lec14 30x30 Al cantilever', [15e3, 4, 900, 30**4 / 12, 15, 70e3, 600, 2, 1, 0],
     lambda: R.SECANT(15e3, 4, 900, 30**4 / 12, 15, 70e3, 600, 2, 1, 0),
     [('SIGMAX=', 0, 44.28, 'Lec14 (src 44.28; exact 44.39, -0.25%)'), ('DELTA MAX=', 0, 4.32, 'Lec14')])
case('SECANT', 'with SY=100 -> FS', [15e3, 4, 900, 30**4 / 12, 15, 70e3, 600, 2, 1, 100],
     lambda: R.SECANT(15e3, 4, 900, 30**4 / 12, 15, 70e3, 600, 2, 1, 100),
     [('FS=SY/SIGMAX', 0, 100 / 44.3889, 'formula')])
case('SECANT', 'guard: P>Pcr', [40e3, 4, 900, 30**4 / 12, 15, 70e3, 600, 2, 1, 0], None, [], ['P≥PCR BUCKLES'])

# ---------------- AISC ----------------
for nm, A, I, L, P, lam, fs in [('Lec14 Burrard DE', .0194, .0005, 13, 1.29, 80.98, 2.64),
                                ('Lec14 Burrard AB', .133, .0118, 12.81, 8.51, 42.99, 3.52),
                                ('Lec14 Burrard FG', .0173, .0003, 15, .33, 113.91, 6.57)]:
    case('AISC', nm, [200e3, 248, A, I, L, 1, P], (lambda A=A, I=I, L=L, P=P: R.AISC(200e3, 248, A, I, 0, L, 1, P)),
         [('LAMBDA=KL/R', 0, lam, 'Lec14 table'), ('FS AISC=', 0, fs, 'Lec14 table'), ('LAMBDA LONG=', 0, 4.71 * math.sqrt(200e3 / 248), 'formula=133.76; Lec14 prints 137.8 (src error)')],
         ['OK FS≥1.67'])
lam_long = 4.71 * math.sqrt(200e3 / 248)
for nm, lam in [('continuity just below lam_long', lam_long * 0.9999), ('long branch', lam_long * 1.5)]:
    r = 1.0; sc = math.pi**2 * 200e3 / lam**2
    exp = (.658**(248 / sc) * 248) if lam < lam_long else .877 * sc
    case('AISC', nm, [200e3, 248, 1, 0, r, lam, 1, 100], None,
         [('SIG FAIL AISC=', 0, exp, 'formula'), ('SIG FAIL AISC=', 0, .877 * math.pi**2 * 248 / 4.71**2 if lam < lam_long else exp,
                                                  'continuity: 0.877*sigcr at lam_long')])

# ---------------- PLAST1 ----------------
case('PLAST1', 'Lec16 2.3 pi-shape', [3, 10, 50, 35, 10, 50, 35, 50, 10, 5, 1],
     lambda: R.PLAST1([(10, 50, 35), (10, 50, 35), (50, 10, 5)], 1),
     [('YBAR ELASTIC=', 0, 25, 'Lec16'), ('YP PLASTIC NA=', 0, 22.5, 'Lec16 fig: 37.5 above / 22.5 below'),
      ('IX=', 0, 2 * 104166.67 + 4166.67 + 300000, 'Lec16 table sum'),
      ('SX=IX/YMAX', 0, 512500 / 35, 'hand'), ('ZX=QAB-QBELOW', 0, 24375, 'hand'), ('K=ZX/SX', 0, 24375 * 35 / 512500, 'hand (1.6646)')])
case('PLAST1', 'rectangle k=1.5', [1, 50, 120, 60, 220], lambda: R.PLAST1([(50, 120, 60)], 220),
     [('K=ZX/SX', 0, 1.5, 'theory'), ('MP=', 0, 220 * 50 * 120**2 / 4, 'theory')])
case('PLAST1', 'Lec16 flanged I (sym check)', [3, 8, .5, 9.75, .5, 9, 5, 8, .5, .25, 36], None,
     [('K=ZX/SX', 0, 1.1402, 'Lec16'), ('MP=', 0, 1732.5, 'Lec16'), ('YP PLASTIC NA=', 0, 5, 'symmetry')])


# ---------------- MOHR ----------------
def mohr_expect(sx, sy, t, th):
    S = np.array([[sx, t], [t, sy]]); c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
    Q = np.array([[c, s], [-s, c]]); Sp = Q @ S @ Q.T
    e = sorted(np.linalg.eigvalsh(S), reverse=True)
    p3 = sorted([e[0], e[1], 0.0])
    return [('SX ROT=', 0, Sp[0, 0], 'Q S Qᵀ'), ('SY ROT=', 0, Sp[1, 1], 'Q S Qᵀ'), ('TXY ROT=', 0, Sp[0, 1], 'Q S Qᵀ'),
            ('S1=', 0, e[0], 'eigvals'), ('S2=', 0, e[1], 'eigvals'), ('TMAX ABS(S3=0)', 0, (p3[2] - p3[0]) / 2, '3-D'),
            ('VON MISES=', 0, math.sqrt(((e[0] - e[1])**2 + e[0]**2 + e[1]**2) / 2), 'VM def')]
for args in [(80, -40, 30, 30), (-80, 50, -25, -30), (50, 20, 10, 75)]:
    case('MOHR', f'sx,sy,txy,th={args}', list(args), (lambda a=args: R.MOHR(*a)), mohr_expect(*args))
case('MOHR', 'thetap rotates to S1', [80, -40, 30, R.MOHR(80, -40, 30, 0)['THETAP TO S1=']], None,
     [('SX ROT=', 0, R.MOHR(80, -40, 30, 0)['S1='], 'principal'), ('TXY ROT=', 0, 0.0, 'principal')])


def close(a, b):
    return abs(a - b) <= TOL * abs(b) + 1e-9


def main(progs):
    rows, fails = [], 0
    for prog, name, ti, ref, checks, msgs in CASES:
        if progs and prog not in progs:
            continue
        try:
            res = tibasic.run(os.path.join(HERE, prog + '.txt'), ti); err = None
        except Exception as e:
            res, err = None, f'{type(e).__name__}: {e}'
        refo = ref() if ref else None
        for m in msgs:
            ok = res is not None and m in res.messages
            fails += not ok
            rows.append((prog, name, 'msg', repr(m), '', 'shown' if ok else 'MISSING', '', 'PASS' if ok else 'FAIL', ''))
        for label, idx, exp, src in checks:
            got = res.outputs.get(label, [None] * (idx + 1))[idx] if res else None
            rv = None
            if refo is not None:
                rv = refo.get(label); rv = rv[idx] if isinstance(rv, list) else rv
            ok = got is not None and close(got, exp) and (refo is None or (rv is not None and close(rv, exp)))
            fails += not ok
            dev = f'{(got - exp) / exp * 100:+.3f}%' if (got is not None and exp) else ''
            rows.append((prog, name, label, f'{exp:.6g}', f'{got:.6g}' if got is not None else (err or 'none'),
                         f'{rv:.6g}' if rv is not None else '-', dev, 'PASS' if ok else 'FAIL', src))
    w = [7, 28, 17, 11, 11, 11, 9, 4]
    hdr = ('prog', 'case', 'output', 'expected', 'TI .txt', 'ref.py', 'dev', 'res', 'source')
    print(' | '.join(h.ljust(x) for h, x in zip(hdr, w + [0])))
    for r in rows:
        print(' | '.join(str(c).ljust(x) for c, x in zip(r, w + [0])))
    print(f'\n{len(rows) - fails}/{len(rows)} checks passed')
    return fails


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1:]) else 0)
