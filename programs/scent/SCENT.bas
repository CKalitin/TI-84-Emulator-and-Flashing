ClrHome
Disp "SHEAR CENTRE","T TO 0,PER THICK","Q/T=C0+C1S+C2S²","R+ IF FLOW CCW","ABOUT PIVOT"
Input "I/T=",I
Input "NO. SEGS=",N
0→E
For(K,1,N)
Disp "SEGMENT",K
Input "C0=",A
Input "C1=",B
Input "C2=",C
Input "LENGTH L=",L
Input "ARM R=",R
(A*L+B*L²/2+C*L³/3)/I→F
Disp "F/V=",F
E+R*F→E
End
Disp "E=SUM(R*F/V)",E,"(V*E=SUM R*F)"
