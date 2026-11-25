"""Python transliteration of every TI-BASIC program (same math, same output labels).
Each function takes the same inputs in the same order as the calculator prompts
(menu choices included) and returns {output label: value}."""
from math import pi, sqrt, cos, atan2, degrees


def PLAST(sec, *a):
    # sec: 1 rect (B,H,E,SY,given,val) 2 I-beam (BF,TF,TW,H,...) 3 box (B,H,T,...)
    if sec == 1:
        B, H, E, S, giv, val = a; W, T = B, 0.0
    elif sec == 2:
        B, T, W, H, E, S, giv, val = a
    else:
        B, H, T, E, S, giv, val = a; W = 2 * T
    C = H / 2; D = C - T
    X = (B * H**3 - (B - W) * (H - 2 * T)**3) / 12
    G = X / C
    Z = B * T * (H - T) + W * D**2
    F = S * G; P = S * Z
    o = {'IX=': X, 'SX=IX/C': G, 'ZX=': Z, 'K=ZX/SX': Z / G, 'MY=': F, 'MP=': P,
         '(YIELD HITS FLG)': S * (B * T * (H - T) + W * D**2 - W * D**2 / 3)}

    def q(Y):
        if Y <= D:
            return B * T * (H - T) + W * D**2 - W * Y**2 / 3
        return B * C**2 - B * Y**2 / 3 - 2 * (B - W) * D**3 / (3 * Y)
    if giv == 1:
        Y = val
        if Y > C:
            return o
        M = S * q(Y); o['M='] = M
    elif giv == 2:
        M = val
        if M <= F or M >= P:
            return o
        L, U = 0.0, C
        for _ in range(45):
            Y = (L + U) / 2
            if S * q(Y) > M: L = Y
            else: U = Y
        o['YY='] = Y
    else:
        return o
    o['RHO LOAD=EYY/SY'] = E * Y / S
    A = M * C / X
    o['SIG UNLOAD(C)='] = A
    o['SRES(C)='] = A - S
    o['SRES(YY)='] = M * Y / X - S
    o['SRES=0 AT Y='] = S * X / M
    o['RHO RESID='] = E * Y / (S - M * Y / X)
    return o


def SCENT(Ip, segs):
    """segs: list of (c0, c1, c2, L, r)."""
    o = {'F/V=': []}; E = 0.0
    for A, B, C, L, R in segs:
        F = (A * L + B * L**2 / 2 + C * L**3 / 3) / Ip
        o['F/V='].append(F); E += R * F
    o['E=SUM(R*F/V)'] = E
    return o


KMENU = {1: .5, 2: .699155, 3: 1, 4: 1, 5: 2, 6: 2}


def EULER_RATIO(kold, knew):
    return {'PCR NEW/OLD=': (kold / knew)**2}


def EULER(E, A, I, R, L, kchoice, Kcustom, N, S, P):
    if I == 0:
        I = R**2 * A
    R = sqrt(I / A)
    K = Kcustom if kchoice == 7 else KMENU[kchoice]
    G = K * L / R
    Q = N**2 * pi**2 * E * I / (K * L)**2
    C = Q / A
    o = {'RGYR=': R, 'LAMBDA=KL/R': G, 'PCR=': Q, 'SIGCR=': C}
    if S > 0:
        o['LAMBDA CROSS='] = pi / sqrt(S / E)
    if P > 0:
        o['FS BUCK=PCR/P'] = Q / P
        if S > 0:
            o['FS YIELD='] = S * A / P; o['FS EULER='] = min(C, S) * A / P
    return o


def SECT(rects):
    """rects: list of (b, h, xc, yc); negative b = hole."""
    A = M = Q = U = V = W = 0.0
    for B, H, X, Y in rects:
        F = B * H
        A += F; M += F * X; Q += F * Y
        U += B * H**3 / 12 + F * Y**2
        V += H * B**3 / 12 + F * X**2
        W += F * X * Y
    X = M / A; Y = Q / A
    U -= A * Y**2; V -= A * X**2
    W = -(W - A * X * Y)
    C = (U + V) / 2; R = sqrt(((U - V) / 2)**2 + W**2)
    return {'A=': A, 'XBAR=': X, 'YBAR=': Y, 'IX=': U, 'IY=': V, 'IXY=-INT(XY)DA': W,
            'IU=C+R (MAX)': C + R, 'IV=C-R (MIN)': C - R,
            'TO IU AXIS': degrees(atan2(2 * W, U - V)) / 2}


def SHEAR_Q(V, I, areas, T):
    Q = sum(a * y for a, y in areas)
    F = V * Q / I
    return {'Q=SUM(A*Y)': Q, 'SHEAR FLOW q=': F, 'TAU AV=q/T': F / T}


def SHEAR_FAST(q, V, Q, I, N, Fa, S):
    o = {}
    F = q
    if q == 0:
        F = V * Q / I; o['q='] = F
    if Fa > 0: o['MAX SPACING='] = N * Fa / F
    if S > 0: o['F PER FASTENER='] = F * S / N
    return o


def SHEAR_2(Vmy, Vx, Qx, Ix, Qy, Iy, T):
    A = abs(Vmy * Qx / Ix); B = abs(Vx * Qy / Iy)
    return {'q FROM V-Y=': A, 'q FROM VX=': B, 'q REINFORCE=': A + B, 'TAU REINF=': (A + B) / T,
            'q OPPOSE=': abs(A - B), 'TAU OPPOSE=': abs(A - B) / T}


def SECANT(P, D, A, I, C, E, L, K, N, S):
    Q = N**2 * pi**2 * E * I / (K * L)**2
    o = {'PCR=': Q, 'P/PCR=': P / Q}
    if P >= Q:
        return o
    Z = pi / 2 * sqrt(P / Q); G = 1 / cos(Z)
    M = P / A * (1 + D * C * A / I * G)
    o.update({'SIGMAX=': M, 'DELTA MAX=': D * (G - 1)})
    if S > 0: o['FS=SY/SIGMAX'] = S / M
    return o


def AISC(E, S, A, I, R, L, K, P):
    if I == 0: I = R**2 * A
    R = sqrt(I / A)
    G = K * L / R; H = 4.71 * sqrt(E / S); C = pi**2 * E / G**2
    F = .658**(S / C) * S if G < H else .877 * C
    return {'LAMBDA=KL/R': G, 'LAMBDA LONG=': H, 'SIGCR EULER=': C, 'SIG FAIL AISC=': F,
            'P/A=': P / A, 'FS AISC=': F * A / P}


def PLAST1(rects, S):
    """rects: list of (b, h, yc)."""
    A = sum(b * h for b, h, y in rects); Y = sum(b * h * y for b, h, y in rects) / A
    I = sum(b * h**3 / 12 + b * h * (y - Y)**2 for b, h, y in rects)
    C = max(max(abs(y + h / 2 - Y), abs(y - h / 2 - Y)) for b, h, y in rects)
    L = min(y - h / 2 for b, h, y in rects); U = max(y + h / 2 for b, h, y in rects)
    for _ in range(45):
        P = (L + U) / 2
        G = sum(b * min(max(P - y + h / 2, 0), h) for b, h, y in rects)
        if G < A / 2: L = P
        else: U = P
    Z = 0.0
    for b, h, y in rects:
        u = y + h / 2 - P; l = y - h / 2 - P
        Z += b * (u * abs(u) - l * abs(l)) / 2
    F = I / C
    return {'A=': A, 'YBAR ELASTIC=': Y, 'IX=': I, 'SX=IX/YMAX': F, 'YP PLASTIC NA=': P,
            'ZX=QAB-QBELOW': Z, 'K=ZX/SX': Z / F, 'MY=': S * F, 'MP=': S * Z}


def MOHR(X, Y, T, th):
    from math import sin, cos, radians
    t = radians(th)
    C = (X + Y) / 2; D = (X - Y) / 2; R = sqrt(D**2 + T**2)
    A, B = C + R, C - R
    M = max(abs(A - B), abs(A), abs(B))
    return {'SX ROT=': C + D * cos(2 * t) + T * sin(2 * t), 'SY ROT=': C - D * cos(2 * t) - T * sin(2 * t),
            'TXY ROT=': -D * sin(2 * t) + T * cos(2 * t), 'S1=': A, 'S2=': B, 'TMAX INPLANE=': R,
            'THETAP TO S1=': degrees(atan2(T, D)) / 2, 'TMAX ABS(S3=0)': M / 2, 'TRESCA=': M,
            'VON MISES=': sqrt(A * A - A * B + B * B)}
