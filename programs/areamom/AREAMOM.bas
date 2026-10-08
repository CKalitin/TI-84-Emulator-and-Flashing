ClrHome
Menu("AREA MOMENTS","MATRIX",M,"TYPE CENTROIDS",T,"TYPE VERTICES",V)
Lbl T
{1}→ʟMK
Goto S
Lbl V
{2}→ʟMK
Lbl S
ClrHome
Disp "AREA MOMENTS"
Input "SHAPES? ",Str1
{expr(Str1),1,ʟMK(1)}→ʟMK
If ʟMK(1)<1 or ʟMK(1)>99 or fPart(ʟMK(1))
Then
Disp "NEED 1-99 SHAPES"
Stop
End
ʟMK(1)→dim(ʟMB)
ʟMK(1)→dim(ʟMH)
ʟMK(1)→dim(ʟMX)
ʟMK(1)→dim(ʟMY)
Repeat ʟMK(2)>ʟMK(1)
ClrHome
Disp ""
Output(1,1,"SHAPE")
Output(1,7,ʟMK(2))
Repeat ʟMB(ʟMK(2))≠0
Input "B=",Str1
expr(Str1)→ʟMB(ʟMK(2))
If not(ʟMB(ʟMK(2)))
Disp "B MUST NOT BE 0"
End
Repeat ʟMH(ʟMK(2)) and (ʟMB(ʟMK(2))>0 or ʟMH(ʟMK(2))>0)
Input "H=",Str1
expr(Str1)→ʟMH(ʟMK(2))
If not(ʟMH(ʟMK(2)))
Disp "H MUST NOT BE 0"
If ʟMB(ʟMK(2))<0 and ʟMH(ʟMK(2))<0
Disp "ONLY B OR H <0"
End
If ʟMK(3)=1
Then
Input "X₀*=",Str1
expr(Str1)→ʟMX(ʟMK(2))
Input "Y₀*=",Str1
expr(Str1)→ʟMY(ʟMK(2))
Else
Input "X1=",Str1
expr(Str1)→ʟMX(ʟMK(2))
Input "Y1=",Str1
expr(Str1)→ʟMY(ʟMK(2))
Input "X2=",Str1
(ʟMX(ʟMK(2))+expr(Str1))/2→ʟMX(ʟMK(2))
Input "Y2=",Str1
(ʟMY(ʟMK(2))+expr(Str1))/2→ʟMY(ʟMK(2))
End
ʟMK(2)+1→ʟMK(2)
End
Goto C
Lbl M
ClrHome
Disp "ROWS: SHAPES","COL:B H X₀* Y₀*","OR:B H X1Y1X2Y2"
Input "MATRIX A-J? ",Str1
{0,0}→ʟMT
If Str1="A":Then:dim([A])→ʟMT:If ʟMT(2)=4:Matr►list([A],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([A],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If Str1="B":Then:dim([B])→ʟMT:If ʟMT(2)=4:Matr►list([B],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([B],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If Str1="C":Then:dim([C])→ʟMT:If ʟMT(2)=4:Matr►list([C],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([C],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If Str1="D":Then:dim([D])→ʟMT:If ʟMT(2)=4:Matr►list([D],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([D],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If Str1="E":Then:dim([E])→ʟMT:If ʟMT(2)=4:Matr►list([E],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([E],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If Str1="F":Then:dim([F])→ʟMT:If ʟMT(2)=4:Matr►list([F],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([F],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If Str1="G":Then:dim([G])→ʟMT:If ʟMT(2)=4:Matr►list([G],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([G],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If Str1="H":Then:dim([H])→ʟMT:If ʟMT(2)=4:Matr►list([H],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([H],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If Str1="I":Then:dim([I])→ʟMT:If ʟMT(2)=4:Matr►list([I],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([I],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If Str1="J":Then:dim([J])→ʟMT:If ʟMT(2)=4:Matr►list([J],ʟMB,ʟMH,ʟMX,ʟMY):If ʟMT(2)=6:Matr►list([J],ʟMB,ʟMH,ʟMX,ʟMY,ʟMV,ʟMW):End
If not(ʟMT(1))
Then
Disp "NAME MUST BE A-J"
Stop
End
If ʟMT(2)≠4 and ʟMT(2)≠6
Then
Disp "4 OR 6 COLUMNS:","B H X₀* Y₀*","B H X1Y1X2Y2"
Stop
End
If ʟMT(1)>99
Then
Disp "MAX 99 ROWS"
Stop
End
If ʟMT(2)=6
Then
(ʟMX+ʟMV)/2→ʟMX
(ʟMY+ʟMW)/2→ʟMY
End
not(ʟMB*ʟMH)+2(ʟMB<0 and ʟMH<0)→ʟMT
If max(ʟMT)
Then
Disp "BAD ROW:",1+sum(cumSum(ʟMT)=0)
If ʟMT(1+sum(cumSum(ʟMT)=0))=1
Disp "B OR H IS 0"
If ʟMT(1+sum(cumSum(ʟMT)=0))=2
Disp "B AND H BOTH <0"
Stop
End
{dim(ʟMB),1,1}→ʟMK
Lbl C
ʟMB*ʟMH→ʟMA
{sum(ʟMA)}→ʟMOA
If ʟMOA(1)≤0
Then
ClrHome
Disp "TOTAL AREA ≤0"
Stop
End
augment(ʟMOA,{sum(ʟMX*ʟMA)/ʟMOA(1),sum(ʟMY*ʟMA)/ʟMOA(1)})→ʟMOA
ʟMX-ʟMOA(2)→ʟMDX
ʟMY-ʟMOA(3)→ʟMDY
ʟMDX*(abs(ʟMDX)≥10^(⁻10)(max(abs(ʟMX))+max(abs(ʟMB))))→ʟMDX
ʟMDY*(abs(ʟMDY)≥10^(⁻10)(max(abs(ʟMY))+max(abs(ʟMH))))→ʟMDY
ʟMB*ʟMH³/12→ʟMIX
ʟMB³*ʟMH/12→ʟMIY
ʟMDY²*ʟMA→ʟMTX
ʟMDX²*ʟMA→ʟMTY
⁻ʟMDX*ʟMDY*ʟMA→ʟMTXY
augment(ʟMOA,{sum(ʟMIX)+sum(ʟMTX),sum(ʟMIY)+sum(ʟMTY),sum(ʟMTXY)})→ʟMOA
If abs(ʟMOA(6))<10^(⁻10)abs(ʟMOA(4)+ʟMOA(5))
0→ʟMOA(6)
augment(ʟMOA,{(ʟMOA(4)+ʟMOA(5))/2,√(((ʟMOA(4)-ʟMOA(5))/2)²+ʟMOA(6)²)})→ʟMOA
If ʟMOA(8)<10^(⁻10)abs(ʟMOA(7))
0→ʟMOA(8)
augment(ʟMOA,{ʟMOA(7)+ʟMOA(8),ʟMOA(7)-ʟMOA(8),0})→ʟMOA
If ʟMOA(8)
R►Pθ(ʟMOA(4)-ʟMOA(5),2ʟMOA(6))*45/R►Pθ(0,1)→ʟMOA(11)
[[ʟMOA(4),ʟMOA(6)][ʟMOA(6),ʟMOA(5)]]→[I]
1→ʟMK(2)
Repeat ʟMK(2)>ʟMK(1)+2
ClrHome
If ʟMK(2)≤ʟMK(1)
Then
Output(1,1,"#")
Output(1,2,ʟMK(2))
Output(1,5,"A=")
Output(2,1,"I_x=")
Output(3,1,"I_y=")
Output(4,1,"Δx₀*=")
Output(5,1,"Δy₀*=")
Output(6,1,"Δy²A=")
Output(7,1,"Δx²A=")
Output(8,1,"-ΔxΔyA=")
{ʟMA(ʟMK(2)),ʟMIX(ʟMK(2)),ʟMIY(ʟMK(2)),ʟMDX(ʟMK(2)),ʟMDY(ʟMK(2)),ʟMTX(ʟMK(2)),ʟMTY(ʟMK(2)),ʟMTXY(ʟMK(2))}→ʟMV
{9,12,12,11,11,11,11,9}→ʟMW
{15,16,16,16,16,16,16,16}→ʟME
{1,1,1,1,1,1,1,1}→ʟMM
End
If ʟMK(2)=ʟMK(1)+1
Then
Output(1,1,"TOTAL (IN [I])")
Output(3,1,"ΣA=")
Output(4,1,"x₀*=")
Output(5,1,"y₀*=")
Output(6,1,"I_x=")
Output(7,1,"I_y=")
Output(8,1,"I_xy=")
augment({0,0},ʟMOA)→ʟMV
8→dim(ʟMV)
{16,16,13,12,12,12,12,11}→ʟMW
{16,16,16,16,16,16,16,16}→ʟME
{0,0,1,1,1,1,1,1}→ʟMM
End
If ʟMK(2)=ʟMK(1)+2
Then
Output(1,1,"PRINCIPAL")
Output(3,1,"I_O=")
Output(4,1,"R=")
Output(5,1,"I_str=")
Output(6,1,"I_wk=")
Output(7,1,"β=")
Output(8,1,"β:x TO STR,CCW")
{0,0,ʟMOA(7),ʟMOA(8),ʟMOA(9),ʟMOA(10),ʟMOA(11),0}→ʟMV
{16,16,12,14,10,11,13,16}→ʟMW
{16,16,16,16,16,16,15,16}→ʟME
{0,0,1,1,1,1,ʟMOA(8)≠0,0}→ʟMM
If ʟMOA(8)
Output(7,16,"°")
If not(ʟMOA(8))
Output(7,3,"ANY AXIS")
End
6+0ʟMV→ʟMS
Repeat max(ʟMZ-ʟMW)≤0
int(log(abs(ʟMV)+not(ʟMV)))→ʟMQ
round(ʟMV*10^(ʟMS-1-ʟMQ),0)*10^(ʟMQ-ʟMS+1)→ʟMT
int(log(abs(ʟMT)+not(ʟMT)))→ʟMQ
round(abs(ʟMT)*10^(ʟMS-1-ʟMQ),0)→ʟMN
ʟMS-(ʟMS>1)(fPart(ʟMN/10)=0)-(ʟMS>2)(fPart(ʟMN/100)=0)-(ʟMS>3)(fPart(ʟMN/1000)=0)-(ʟMS>4)(fPart(ʟMN/10000)=0)-(ʟMS>5)(fPart(ʟMN/100000)=0)→ʟMN
(ʟMQ≥10 or ʟMQ≤⁻4)→ʟMZ
(ʟMT<0)+ʟMZ*(ʟMN+(ʟMN>1)+2+(ʟMQ<0)+(abs(ʟMQ)≥10))+not(ʟMZ)*((ʟMQ≥0)*(max(ʟMQ+1,ʟMN)+(ʟMN>ʟMQ+1))+(ʟMQ<0)*(ʟMN-ʟMQ))→ʟMZ
max(1,ʟMS-(ʟMZ>ʟMW)*max(1,ʟMZ-ʟMW))→ʟMS
End
If ʟMM(1)
Output(1,ʟME(1)-ʟMZ(1)+1,ʟMT(1))
If ʟMM(2)
Output(2,ʟME(2)-ʟMZ(2)+1,ʟMT(2))
If ʟMM(3)
Output(3,ʟME(3)-ʟMZ(3)+1,ʟMT(3))
If ʟMM(4)
Output(4,ʟME(4)-ʟMZ(4)+1,ʟMT(4))
If ʟMM(5)
Output(5,ʟME(5)-ʟMZ(5)+1,ʟMT(5))
If ʟMM(6)
Output(6,ʟME(6)-ʟMZ(6)+1,ʟMT(6))
If ʟMM(7)
Output(7,ʟME(7)-ʟMZ(7)+1,ʟMT(7))
If ʟMM(8)
Output(8,ʟME(8)-ʟMZ(8)+1,ʟMT(8))
If ʟMK(2)≤ʟMK(1)+1
Pause :ʟMK(2)+1→ʟMK(2)
End
DelVar ʟMV:DelVar ʟMW:DelVar ʟME:DelVar ʟMM:DelVar ʟMS
DelVar ʟMT:DelVar ʟMQ:DelVar ʟMN:DelVar ʟMZ:DelVar ʟMK
""
