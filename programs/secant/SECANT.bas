Radian
ClrHome
Disp "SECANT FORMULA","CONSISTENT UNITS","NOT FIX-FIX,","FIX-GUID,FIX-PIN"
Input "P COMPR=",P
Input "ECCENTR E=",D
Input "AREA A=",A
Input "I=",I
Input "C=|Y|MAX=",C
Input "MODULUS E=",E
Input "LENGTH L=",L
Input "K=",K
Input "MODE N=",N
Input "SY(0=SKIP)=",S
N²*pi²*E*I/(K*L)²→Q
ClrHome
Disp "PCR=",Q,"P/PCR=",P/Q
If P≥Q
Then
Disp "P≥PCR BUCKLES"
Stop
End
pi/2*√(P/Q)→Z
1/cos(Z)→G
P/A*(1+D*C*A/I*G)→M
Disp "SIGMAX=",M,"DELTA MAX=",D*(G-1)
If S>0
Then
Pause
Disp "FS=SY/SIGMAX",S/M
End
