ClrHome
Disp "FULLY PLASTIC","SYM ABOUT VERT","RECTS B,H,YC","YC ANY DATUM"
Input "NO. RECTS=",N
N→dim(L₁)
N→dim(L₂)
N→dim(L₃)
0→A
0→Q
For(K,1,N)
Disp "RECT",K
Input "B=",B
Input "H=",H
Input "YC=",Y
B→L₁(K)
H→L₂(K)
Y→L₃(K)
A+B*H→A
Q+B*H*Y→Q
End
Input "SIGY=",S
Q/A→Y
0→I
0→C
L₃(1)-L₂(1)/2→L
L₃(1)+L₂(1)/2→U
For(K,1,N)
L₁(K)→B
L₂(K)→H
L₃(K)→D
I+B*H³/12+B*H*(D-Y)²→I
max(C,abs(D+H/2-Y))→C
max(C,abs(D-H/2-Y))→C
min(L,D-H/2)→L
max(U,D+H/2)→U
End
For(J,1,45)
(L+U)/2→P
0→G
For(K,1,N)
G+L₁(K)*min(max(P-L₃(K)+L₂(K)/2,0),L₂(K))→G
End
If G<A/2
Then
P→L
Else
P→U
End
End
0→Z
For(K,1,N)
L₃(K)+L₂(K)/2-P→U
L₃(K)-L₂(K)/2-P→L
Z+L₁(K)*(U*abs(U)-L*abs(L))/2→Z
End
I/C→F
ClrHome
Disp "A=",A,"YBAR ELASTIC=",Y,"IX=",I,"SX=IX/YMAX",F
Pause
Disp "YP PLASTIC NA=",P,"ZX=QAB-QBELOW",Z,"K=ZX/SX",Z/F
Pause
Disp "MY=",S*F,"MP=",S*Z
