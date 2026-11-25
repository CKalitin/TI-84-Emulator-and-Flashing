ClrHome
Disp "EULER BUCKLING","CONSISTENT UNITS"
Menu("EULER","COLUMN",A,"K RATIO",R)
Lbl R
Input "K OLD=",O
Input "K NEW=",N
Disp "PCR NEW/OLD=",(O/N)²
Stop
Lbl A
Input "E=",E
Input "AREA A=",A
Input "I(0=USE R)=",I
If I=0
Then
Input "RGYR=",R
R²*A→I
End
√(I/A)→R
Input "LENGTH L=",L
Menu("END CONDITION","FIX-FIX K=.5",1,"FIX-PIN K=.699",2,"PIN-PIN K=1",3,"FIX-GUID K=1",3,"FIX-FREE K=2",4,"PIN-GUID K=2",4,"CUSTOM K",5)
Lbl 1
.5→K
Goto 6
Lbl 2
.699155→K
Goto 6
Lbl 3
1→K
Goto 6
Lbl 4
2→K
Goto 6
Lbl 5
Input "K=",K
Lbl 6
Input "MODE N=",N
Input "SY(0=SKIP)=",S
Input "P(0=SKIP)=",P
K*L/R→G
N²*pi²*E*I/(K*L)²→Q
Q/A→C
ClrHome
Disp "RGYR=",R,"LAMBDA=KL/R",G,"PCR=",Q,"SIGCR=",C
Pause
If S>0
Then
Disp "LAMBDA CROSS=",pi/√(S/E)
If C>S
Disp "SIGCR>SY","YIELDS FIRST"
End
If P>0
Then
Pause
Disp "FS BUCK=PCR/P",Q/P
If S>0
Disp "FS YIELD=",S*A/P,"FS EULER=",min(C,S)*A/P
End
