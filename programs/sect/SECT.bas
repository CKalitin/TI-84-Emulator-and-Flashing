Degree
ClrHome
Disp "COMPOSITE RECTS","XC,YC ANY DATUM","HOLE NEGATIVE B"
Input "NO. RECTS=",N
0→A
0→M
0→Q
0→U
0→V
0→W
For(K,1,N)
Disp "RECT",K
Input "B(NEG=HOLE)=",B
Input "H=",H
Input "XC=",X
Input "YC=",Y
B*H→F
A+F→A
M+F*X→M
Q+F*Y→Q
U+B*H³/12+F*Y²→U
V+H*B³/12+F*X²→V
W+F*X*Y→W
End
M/A→X
Q/A→Y
U-A*Y²→U
V-A*X²→V
⁻(W-A*X*Y)→W
ClrHome
Disp "A=",A,"XBAR=",X,"YBAR=",Y
Pause
Disp "IX=",U,"IY=",V,"IXY=-INT(XY)DA",W
Pause
(U+V)/2→C
√(((U-V)/2)²+W²)→R
Disp "IU=C+R (MAX)",C+R,"IV=C-R (MIN)",C-R,"BETA DEG CCW X","TO IU AXIS",R►Pθ(U-V,2*W)/2
