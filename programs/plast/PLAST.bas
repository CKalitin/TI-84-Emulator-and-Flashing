Radian
ClrHome
Disp "ELASTOPLASTIC","DOUBLY SYMMETRIC","CONSISTENT UNITS"
Menu("SECTION","RECT B*H",1,"I-BEAM",2,"HOLLOW BOX",3)
Lbl 1
Input "B=",B
Input "H=",H
B→W
0→T
Goto 4
Lbl 2
Input "FLANGE BF=",B
Input "FLANGE TF=",T
Input "WEB TW=",W
Input "TOTAL H=",H
Goto 4
Lbl 3
Input "OUTER B=",B
Input "OUTER H=",H
Input "WALL T=",T
2*T→W
Lbl 4
Input "E=",E
Input "SIGY=",S
H/2→C
C-T→D
(B*H³-(B-W)*(H-2*T)³)/12→X
X/C→G
B*T*(H-T)+W*D²→Z
S*G→F
S*Z→P
ClrHome
Disp "IX=",X,"SX=IX/C",G,"ZX=",Z,"K=ZX/SX",Z/G
Pause
Disp "MY=",F,"MP=",P,"M WHEN YY=D","(YIELD HITS FLG)",S*(B*T*(H-T)+W*D²-W*D²/3)
Pause
Menu("GIVEN","YY (FIND M)",5,"M (FIND YY)",6,"QUIT",9)
Lbl 5
Input "YY=",Y
If Y>C
Then
Disp "YY>C ELASTIC"
Stop
End
If Y≤D
Then
B*T*(H-T)+W*D²-W*Y²/3→Q
Else
B*C²-B*Y²/3-2*(B-W)*D³/(3*Y)→Q
End
S*Q→M
Disp "M=",M
Goto 7
Lbl 6
Input "M=",M
If M≤F
Then
Disp "M≤MY ELASTIC"
Stop
End
If M≥P
Then
Disp "M≥MP FULLY","PLASTIC"
Stop
End
0→L
C→U
For(I,1,45)
(L+U)/2→Y
If Y≤D
Then
B*T*(H-T)+W*D²-W*Y²/3→Q
Else
B*C²-B*Y²/3-2*(B-W)*D³/(3*Y)→Q
End
If S*Q>M
Then
Y→L
Else
Y→U
End
End
Disp "YY=",Y
If Y≤D
Disp "(YY IN WEB)"
If Y>D
Disp "(YY IN FLANGE)"
Lbl 7
Disp "RHO LOAD=EYY/SY",E*Y/S
Pause
ClrHome
If M>2*F
Disp "M>2MY UNLOAD","NOT ELASTIC!"
M*C/X→A
Disp "RESID=UNLOAD-SY","SIG UNLOAD(C)=",A,"SRES(C)=",A-S,"SRES(YY)=",M*Y/X-S
Pause
Disp "SRES=0 AT Y=",S*X/M,"RHO RESID=",E*Y/(S-M*Y/X)
Lbl 9
