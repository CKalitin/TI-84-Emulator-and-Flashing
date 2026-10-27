ClrHome
Disp "INVARIANTS","σ: 3X3 OR 2X2","SYMMETRIC"
Input "MATRIX A-J? ",Str1
{0,0}→ʟIVT
If Str1="A":Then:dim([A])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([A],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([A],ʟIVX,ʟIVY):End
If Str1="B":Then:dim([B])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([B],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([B],ʟIVX,ʟIVY):End
If Str1="C":Then:dim([C])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([C],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([C],ʟIVX,ʟIVY):End
If Str1="D":Then:dim([D])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([D],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([D],ʟIVX,ʟIVY):End
If Str1="E":Then:dim([E])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([E],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([E],ʟIVX,ʟIVY):End
If Str1="F":Then:dim([F])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([F],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([F],ʟIVX,ʟIVY):End
If Str1="G":Then:dim([G])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([G],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([G],ʟIVX,ʟIVY):End
If Str1="H":Then:dim([H])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([H],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([H],ʟIVX,ʟIVY):End
If Str1="I":Then:dim([I])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([I],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([I],ʟIVX,ʟIVY):End
If Str1="J":Then:dim([J])→ʟIVT:If ʟIVT(1)=3 and ʟIVT(2)=3:Matr►list([J],ʟIVX,ʟIVY,ʟIVZ):If ʟIVT(1)=2 and ʟIVT(2)=2:Matr►list([J],ʟIVX,ʟIVY):End
If not(ʟIVT(1))
Then
Disp "NAME MUST BE A-J"
Goto Q
End
If ʟIVT(1)≠ʟIVT(2) or ʟIVT(1)<2 or ʟIVT(1)>3
Then
Disp "NEED 3X3 OR 2X2","GOT",ʟIVT
Goto Q
End
If ʟIVT(1)=2
Then
{ʟIVX(1),ʟIVY(2),0,ʟIVY(1),0,0,ʟIVX(2),0,0}→ʟIVS
Else
{ʟIVX(1),ʟIVY(2),ʟIVZ(3),ʟIVY(1),ʟIVZ(2),ʟIVZ(1),ʟIVX(2),ʟIVY(3),ʟIVX(3)}→ʟIVS
End
abs({ʟIVS(4)-ʟIVS(7),ʟIVS(5)-ʟIVS(8),ʟIVS(6)-ʟIVS(9)})>10^(⁻9)max(abs(ʟIVS))→ʟIVT
If max(ʟIVT)
Then
Disp "NOT SYMMETRIC:"
If ʟIVT(1)
Disp "(1,2)≠(2,1)"
If ʟIVT(2)
Disp "(2,3)≠(3,2)"
If ʟIVT(3)
Disp "(1,3)≠(3,1)"
Goto Q
End
6→dim(ʟIVS)
{max(abs(ʟIVS))}→ʟIVT
{ʟIVS(1)+ʟIVS(2)+ʟIVS(3),ʟIVS(1)ʟIVS(2)+ʟIVS(2)ʟIVS(3)+ʟIVS(3)ʟIVS(1)-ʟIVS(4)²-ʟIVS(5)²-ʟIVS(6)²,ʟIVS(1)ʟIVS(2)ʟIVS(3)+2ʟIVS(4)ʟIVS(5)ʟIVS(6)-ʟIVS(1)ʟIVS(5)²-ʟIVS(2)ʟIVS(6)²-ʟIVS(3)ʟIVS(4)²,((ʟIVS(1)-ʟIVS(2))²+(ʟIVS(2)-ʟIVS(3))²+(ʟIVS(3)-ʟIVS(1))²)/6+ʟIVS(4)²+ʟIVS(5)²+ʟIVS(6)²}→ʟIVAR
augment({ʟIVS(1),ʟIVS(2),ʟIVS(3)}-ʟIVAR(1)/3,{ʟIVS(4),ʟIVS(5),ʟIVS(6)})→ʟIVS
augment(ʟIVAR,{ʟIVS(1)ʟIVS(2)ʟIVS(3)+2ʟIVS(4)ʟIVS(5)ʟIVS(6)-ʟIVS(1)ʟIVS(5)²-ʟIVS(2)ʟIVS(6)²-ʟIVS(3)ʟIVS(4)²})→ʟIVAR
ʟIVAR*(abs(ʟIVAR)≥10^(⁻12)ʟIVT(1)^{1,2,3,2,3})→ʟIVAR
6+0ʟIVAR→ʟIVG
Repeat max(ʟIVF)≤12
int(log(abs(ʟIVAR)+not(ʟIVAR)))→ʟIVQ
round(ʟIVAR*10^(ʟIVG-1-ʟIVQ),0)*10^(ʟIVQ-ʟIVG+1)→ʟIVR
int(log(abs(ʟIVR)+not(ʟIVR)))→ʟIVQ
round(abs(ʟIVR)*10^(ʟIVG-1-ʟIVQ),0)→ʟIVN
ʟIVG-(ʟIVG>1)(fPart(ʟIVN/10)=0)-(ʟIVG>2)(fPart(ʟIVN/100)=0)-(ʟIVG>3)(fPart(ʟIVN/1000)=0)-(ʟIVG>4)(fPart(ʟIVN/10000)=0)-(ʟIVG>5)(fPart(ʟIVN/100000)=0)→ʟIVN
(ʟIVQ≥10 or ʟIVQ≤⁻4)→ʟIVF
(ʟIVR<0)+ʟIVF*(ʟIVN+(ʟIVN>1)+2+(ʟIVQ<0)+(abs(ʟIVQ)≥10))+not(ʟIVF)*((ʟIVQ≥0)*(max(ʟIVQ+1,ʟIVN)+(ʟIVN>ʟIVQ+1))+(ʟIVQ<0)*(ʟIVN-ʟIVQ))→ʟIVF
max(1,ʟIVG-(ʟIVF>12)*max(1,ʟIVF-12))→ʟIVG
End
ClrHome
Output(1,1,"INVARIANTS ["+Str1+"]")
Output(2,1,"(IN ʟIVAR)")
Output(3,1,"I_1=")
Output(4,1,"I_2=")
Output(5,1,"I_3=")
Output(6,1,"J_2=")
Output(7,1,"J_3=")
Output(3,17-ʟIVF(1),ʟIVR(1))
Output(4,17-ʟIVF(2),ʟIVR(2))
Output(5,17-ʟIVF(3),ʟIVR(3))
Output(6,17-ʟIVF(4),ʟIVR(4))
Output(7,17-ʟIVF(5),ʟIVR(5))
Goto Z
Lbl Q
DelVar ʟIVT:DelVar ʟIVX:DelVar ʟIVY:DelVar ʟIVZ:DelVar ʟIVS
DelVar ʟIVG:DelVar ʟIVQ:DelVar ʟIVR:DelVar ʟIVN:DelVar ʟIVF
Stop
Lbl Z
DelVar ʟIVT:DelVar ʟIVX:DelVar ʟIVY:DelVar ʟIVZ:DelVar ʟIVS
DelVar ʟIVG:DelVar ʟIVQ:DelVar ʟIVR:DelVar ʟIVN:DelVar ʟIVF
""
