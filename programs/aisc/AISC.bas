ClrHome
Disp "AISC STEEL COL","CONSISTENT UNITS"
Input "E=",E
Input "SIGY=",S
Input "AREA A=",A
Input "I(0=USE R)=",I
If I=0
Then
Input "RGYR=",R
R²*A→I
End
√(I/A)→R
Input "LENGTH L=",L
Input "K=",K
Input "P COMPR=",P
K*L/R→G
4.71*√(E/S)→H
pi²*E/G²→C
If G<H
Then
.658^(S/C)*S→F
Else
.877*C→F
End
F*A/P→Z
ClrHome
Disp "LAMBDA=KL/R",G,"LAMBDA LONG=",H,"SIGCR EULER=",C,"SIG FAIL AISC=",F
Pause
Disp "P/A=",P/A,"FS AISC=",Z
If Z≥1.67
Disp "OK FS≥1.67"
If Z<1.67
Disp "NOT OK FS<1.67"
