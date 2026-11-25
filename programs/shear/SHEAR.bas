ClrHome
Disp "SHEAR FLOW","CONSISTENT UNITS"
Menu("SHEAR FLOW","Q=VQ/I, TAU",1,"FASTENERS",2,"VX + V-Y",3)
Lbl 1
Input "V=",V
Input "I=",I
Input "NO. AREAS=",N
0→Q
For(K,1,N)
Disp "AREA BEYOND CUT",K
Input "AREA AI=",A
Input "YBAR TO NA=",Y
Q+A*Y→Q
End
Input "CUT THICK T=",T
V*Q/I→F
Disp "Q=SUM(A*Y)",Q,"SHEAR FLOW q=",F,"TAU AV=q/T",F/T
Stop
Lbl 2
Input "q(0=VQ/I)=",F
If F=0
Then
Input "V=",V
Input "Q=",Q
Input "I=",I
V*Q/I→F
Disp "q=",F
End
Input "N PER ROW=",N
Disp "0 = SKIP"
Input "F ALLOW=",A
Input "SPACING S=",S
If A>0
Disp "MAX SPACING=",N*A/F
If S>0
Disp "F PER FASTENER=",F*S/N
Stop
Lbl 3
Input "V-Y=",V
Input "VX=",U
Input "QX=",Q
Input "IX=",I
Input "QY=",P
Input "IY=",J
Input "CUT THICK T=",T
abs(V*Q/I)→A
abs(U*P/J)→B
Disp "q FROM V-Y=",A,"q FROM VX=",B
Pause
Disp "q REINFORCE=",A+B,"TAU REINF=",(A+B)/T,"q OPPOSE=",abs(A-B),"TAU OPPOSE=",abs(A-B)/T
