Degree
ClrHome
Disp "PLANE STRESS","THETA DEG CCW"
Input "SX=",X
Input "SY=",Y
Input "TXY=",T
Input "THETA=",θ
(X+Y)/2→C
(X-Y)/2→D
√(D²+T²)→R
C+D*cos(2*θ)+T*sin(2*θ)→U
C-D*cos(2*θ)-T*sin(2*θ)→V
⁻D*sin(2*θ)+T*cos(2*θ)→W
C+R→A
C-R→B
ClrHome
Disp "SX ROT=",U,"SY ROT=",V,"TXY ROT=",W
Pause
Disp "S1=",A,"S2=",B,"TMAX INPLANE=",R,"THETAP TO S1=",R►Pθ(D,T)/2
Pause
max(abs(A-B),max(abs(A),abs(B)))→M
Disp "TMAX ABS(S3=0)",M/2,"TRESCA=",M,"VON MISES=",√(A²-A*B+B²)
