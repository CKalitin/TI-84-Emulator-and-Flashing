ClrHome
Menu("UNSYM BENDING","FROM AREAMOM",A,"TYPE I VALUES",B)
Lbl A
{ʟMOA(4),ʟMOA(5),ʟMOA(6),ʟMOA(2),ʟMOA(3)}→ʟBSEC
Goto I
Lbl B
ClrHome
Disp "CENTROIDAL, MM","I_xy=-∫xy dA"
{0,0,0,0,0}→ʟBSEC
Input "I_x=",Str1
expr(Str1)→ʟBSEC(1)
Input "I_y=",Str1
expr(Str1)→ʟBSEC(2)
Input "I_xy=",Str1
expr(Str1)→ʟBSEC(3)
Input "X₀*=",Str1
expr(Str1)→ʟBSEC(4)
Input "Y₀*=",Str1
expr(Str1)→ʟBSEC(5)
Lbl I
augment(ʟBSEC,{ʟBSEC(1)ʟBSEC(2)-ʟBSEC(3)²,(ʟBSEC(1)+ʟBSEC(2))/2,√(((ʟBSEC(1)-ʟBSEC(2))/2)²+ʟBSEC(3)²)})→ʟBSEC
If ʟBSEC(8)<10^(⁻10)abs(ʟBSEC(7))
0→ʟBSEC(8)
augment(ʟBSEC,{ʟBSEC(7)+ʟBSEC(8),ʟBSEC(7)-ʟBSEC(8),0,0})→ʟBSEC
If ʟBSEC(10)≤0 or ʟBSEC(6)≤0
Then
ClrHome
Disp "I_v≤0 OR DET≤0:","NOT A REAL","SECTION"
Stop
End
ʟBSEC(9)/ʟBSEC(10)→ʟBSEC(11)
{R►Pθ(0,1)/90,1,2,0,0}→ʟBK
If ʟBSEC(8)
R►Pθ(ʟBSEC(1)-ʟBSEC(2),2ʟBSEC(3))/(2ʟBK(1))→ʟBSEC(12)
{ʟBSEC(2),⁻ʟBSEC(3),ʟBSEC(1),ʟBSEC(3),⁻ʟBSEC(1),ʟBSEC(2),⁻ʟBSEC(3)}/ʟBSEC(6)→ʟBINV
ClrHome
Disp "MOMENTS IN N*M","(BOTH 0: SECTION","ONLY)"
Input "M_x=",Str1
{expr(Str1)}→ʟBMOM
Input "M_y=",Str1
augment(ʟBMOM,{expr(Str1)})→ʟBMOM
If ʟBMOM(1) or ʟBMOM(2)
Then
augment(ʟBMOM,{1000(ʟBINV(4)ʟBMOM(1)+ʟBINV(5)ʟBMOM(2)),1000(ʟBINV(6)ʟBMOM(1)+ʟBINV(7)ʟBMOM(2))})→ʟBMOM
augment(ʟBMOM,{√(ʟBMOM(3)²+ʟBMOM(4)²),R►Pθ(ʟBMOM(1),ʟBMOM(2))/ʟBK(1),R►Pθ(ʟBMOM(3),ʟBMOM(4))/ʟBK(1)})→ʟBMOM
augment(ʟBMOM,{ʟBMOM(6)-ʟBSEC(12)})→ʟBMOM
ʟBMOM(8)+360int((180-ʟBMOM(8))/360)→ʟBMOM(8)
augment(ʟBMOM,{R►Pθ(ʟBSEC(10)cos(ʟBK(1)ʟBMOM(8)),ʟBSEC(9)sin(ʟBK(1)ʟBMOM(8)))/ʟBK(1)})→ʟBMOM
ʟBMOM(9)+180int((90-ʟBMOM(9))/180)→ʟBMOM(9)
augment(ʟBMOM,{ʟBSEC(12)+ʟBMOM(9),ʟBMOM(7)-90,cos(ʟBK(1)ʟBSEC(12))ʟBMOM(1)+sin(ʟBK(1)ʟBSEC(12))ʟBMOM(2),⁻sin(ʟBK(1)ʟBSEC(12))ʟBMOM(1)+cos(ʟBK(1)ʟBSEC(12))ʟBMOM(2)})→ʟBMOM
ʟBMOM(10)+180int((90-ʟBMOM(10))/180)→ʟBMOM(10)
ʟBMOM(11)+180int((90-ʟBMOM(11))/180)→ʟBMOM(11)
ClrHome
Disp "POINTS X,Y (MM):","A-J: MATRIX, ONE","ROW PER POINT","N: TYPE N POINTS","0: NONE"
Input "POINTS? ",Str1
If not(length(Str1))
"0"→Str1
{0,0}→ʟBT
If Str1="A":Then:dim([A])→ʟBT:If ʟBT(2)=2:Matr►list([A],ʟBPX,ʟBPY):End
If Str1="B":Then:dim([B])→ʟBT:If ʟBT(2)=2:Matr►list([B],ʟBPX,ʟBPY):End
If Str1="C":Then:dim([C])→ʟBT:If ʟBT(2)=2:Matr►list([C],ʟBPX,ʟBPY):End
If Str1="D":Then:dim([D])→ʟBT:If ʟBT(2)=2:Matr►list([D],ʟBPX,ʟBPY):End
If Str1="E":Then:dim([E])→ʟBT:If ʟBT(2)=2:Matr►list([E],ʟBPX,ʟBPY):End
If Str1="F":Then:dim([F])→ʟBT:If ʟBT(2)=2:Matr►list([F],ʟBPX,ʟBPY):End
If Str1="G":Then:dim([G])→ʟBT:If ʟBT(2)=2:Matr►list([G],ʟBPX,ʟBPY):End
If Str1="H":Then:dim([H])→ʟBT:If ʟBT(2)=2:Matr►list([H],ʟBPX,ʟBPY):End
If Str1="I":Then:dim([I])→ʟBT:If ʟBT(2)=2:Matr►list([I],ʟBPX,ʟBPY):End
If Str1="J":Then:dim([J])→ʟBT:If ʟBT(2)=2:Matr►list([J],ʟBPX,ʟBPY):End
If ʟBT(1)
Then
If ʟBT(2)≠2
Then
Disp "NEED 2 COLUMNS:","X Y"
Stop
End
If ʟBT(1)>99
Then
Disp "MAX 99 ROWS"
Stop
End
ʟBT(1)→ʟBK(4)
Else
If not(inString("0123456789",sub(Str1,1,1)))
Then
Disp "A-J OR A NUMBER"
Stop
End
expr(Str1)→ʟBK(4)
If ʟBK(4)>99 or fPart(ʟBK(4))
Then
Disp "NEED 0-99 POINTS"
Stop
End
If ʟBK(4)
Then
ʟBK(4)→dim(ʟBPX)
ʟBK(4)→dim(ʟBPY)
Repeat ʟBK(2)>ʟBK(4)
ClrHome
Disp ""
Output(1,1,"POINT")
Output(1,7,ʟBK(2))
Input "X=",Str1
expr(Str1)→ʟBPX(ʟBK(2))
Input "Y=",Str1
expr(Str1)→ʟBPY(ʟBK(2))
ʟBK(2)+1→ʟBK(2)
End
1→ʟBK(2)
End
End
If ʟBK(4)
Then
ʟBPX-ʟBSEC(4)→ʟBPRX
ʟBPY-ʟBSEC(5)→ʟBPRY
cos(ʟBK(1)ʟBSEC(12))ʟBPRX+sin(ʟBK(1)ʟBSEC(12))ʟBPRY→ʟBPU
⁻sin(ʟBK(1)ʟBSEC(12))ʟBPRX+cos(ʟBK(1)ʟBSEC(12))ʟBPRY→ʟBPV
ʟBPRX*ʟBMOM(3)+ʟBPRY*ʟBMOM(4)→ʟBPSZ
1000(⁻ʟBMOM(13)ʟBPU/ʟBSEC(10)+ʟBMOM(12)ʟBPV/ʟBSEC(9))→ʟBPCK
1+sum(cumSum(abs(ʟBPSZ)=max(abs(ʟBPSZ)))=0)→ʟBK(5)
End
4+ʟBK(4)+(ʟBK(4)>0)→ʟBK(3)
End
If not(ʟBK(4))
Then
DelVar ʟBPX:DelVar ʟBPY:DelVar ʟBPRX:DelVar ʟBPRY:DelVar ʟBPU:DelVar ʟBPV:DelVar ʟBPSZ:DelVar ʟBPCK
End
Repeat ʟBK(2)>ʟBK(3)
ClrHome
If ʟBK(2)=1
Then
Output(1,1,"U=STRONG V=WEAK")
Output(2,1,"det=")
Output(3,1,"C=")
Output(4,1,"R=")
Output(5,1,"I_u=")
Output(6,1,"I_v=")
Output(7,1,"I_u/I_v=")
Output(8,1,"β=")
{0,ʟBSEC(6),ʟBSEC(7),ʟBSEC(8),ʟBSEC(9),ʟBSEC(10),ʟBSEC(11),round(ʟBSEC(12),2)}→ʟBFV
{16,12,14,14,12,12,8,13}→ʟBFW
{16,16,16,16,16,16,16,15}→ʟBFE
{0,1,1,1,1,1,1,ʟBSEC(8)≠0}→ʟBFM
If ʟBSEC(8)
Output(8,16,"°")
If not(ʟBSEC(8))
Output(8,3,"ANY AXIS")
End
If ʟBK(2)=2
Then
Output(1,1,"IN=INV(I),1/MM^4")
Output(2,1,"IN11=")
Output(3,1,"IN12=")
Output(4,1,"IN22=")
Output(5,1,"B11=")
Output(6,1,"B12=")
Output(7,1,"B21=")
Output(8,1,"B22=")
augment({0},ʟBINV)→ʟBFV
{16,11,11,11,12,12,12,12}→ʟBFW
{16,16,16,16,16,16,16,16}→ʟBFE
{0,1,1,1,1,1,1,1}→ʟBFM
End
If ʟBK(2)=3
Then
Output(1,1,"GRAD σ_z, MPA/MM")
Output(2,1,"G_x=")
Output(3,1,"G_y=")
Output(4,1,"G_mag=")
Output(5,1,"M ANG=")
Output(6,1,"G ANG=")
Output(7,1,"θ=")
Output(8,1,"α=")
{0,ʟBMOM(3),ʟBMOM(4),ʟBMOM(5),round(ʟBMOM(6),2),round(ʟBMOM(7),2),round(ʟBMOM(8),2),round(ʟBMOM(9),2)}→ʟBFV
{16,12,12,10,9,9,13,13}→ʟBFW
{16,16,16,16,15,15,15,15}→ʟBFE
{0,1,1,1,1,1,1,1}→ʟBFM
Output(5,16,"°")
Output(6,16,"°")
Output(7,16,"°")
Output(8,16,"°")
End
If ʟBK(2)=4
Then
Output(1,1,"NEUTRAL AXIS")
Output(2,1,"NA=")
Output(3,1,"CHK=")
Output(4,1,"M_u=")
Output(5,1,"M_v=")
Output(6,1,"(M_u,M_v: N*M)")
Output(7,1,"θ,α:CCW FROM U")
Output(8,1,"NA,ANG:CCW FRM X")
{0,round(ʟBMOM(10),2),round(ʟBMOM(11),2),ʟBMOM(12),ʟBMOM(13),0,0,0}→ʟBFV
{16,12,11,12,12,16,16,16}→ʟBFW
{16,15,15,16,16,16,16,16}→ʟBFE
{0,1,1,1,1,0,0,0}→ʟBFM
Output(2,16,"°")
Output(3,16,"°")
End
If ʟBK(2)≥5 and ʟBK(2)≤4+ʟBK(4)
Then
ʟBK(2)-4→ʟBT(1)
Output(1,1,"POINT")
Output(1,7,ʟBT(1))
If ʟBT(1)=ʟBK(5)
Output(1,12,"MAX")
Output(2,1,"r_x=")
Output(3,1,"r_y=")
Output(4,1,"u=")
Output(5,1,"v=")
Output(6,1,"σ_z=")
Output(7,1,"CHK=")
{0,ʟBPRX(ʟBT(1)),ʟBPRY(ʟBT(1)),ʟBPU(ʟBT(1)),ʟBPV(ʟBT(1)),ʟBPSZ(ʟBT(1)),ʟBPCK(ʟBT(1)),0}→ʟBFV
{16,12,12,14,14,12,12,16}→ʟBFW
{16,16,16,16,16,16,16,16}→ʟBFE
{0,1,1,1,1,1,1,0}→ʟBFM
End
If ʟBK(4) and ʟBK(2)=5+ʟBK(4)
Then
ʟBK(5)→ʟBT(1)
Output(1,1,"MAX ABS σ_z")
Output(3,1,"POINT=")
Output(4,1,"σ_z=")
Output(6,1,"X=")
Output(7,1,"Y=")
{0,0,ʟBT(1),ʟBPSZ(ʟBT(1)),0,ʟBPX(ʟBT(1)),ʟBPY(ʟBT(1)),0}→ʟBFV
{16,16,10,12,16,14,14,16}→ʟBFW
{16,16,16,16,16,16,16,16}→ʟBFE
{0,0,1,1,0,1,1,0}→ʟBFM
End
If ʟBK(2)≥5 and ʟBK(4)
Then
If ʟBPSZ(ʟBT(1))>0
Output(8,1,"MPA, TENSION")
If ʟBPSZ(ʟBT(1))<0
Output(8,1,"MPA, COMPRESSION")
If not(ʟBPSZ(ʟBT(1)))
Output(8,1,"MPA, ZERO")
End
6+0ʟBFV→ʟBFS
Repeat max(ʟBFZ-ʟBFW)≤0
int(log(abs(ʟBFV)+not(ʟBFV)))→ʟBFQ
round(ʟBFV*10^(ʟBFS-1-ʟBFQ),0)*10^(ʟBFQ-ʟBFS+1)→ʟBFT
int(log(abs(ʟBFT)+not(ʟBFT)))→ʟBFQ
round(abs(ʟBFT)*10^(ʟBFS-1-ʟBFQ),0)→ʟBFN
ʟBFS-(ʟBFS>1)(fPart(ʟBFN/10)=0)-(ʟBFS>2)(fPart(ʟBFN/100)=0)-(ʟBFS>3)(fPart(ʟBFN/1000)=0)-(ʟBFS>4)(fPart(ʟBFN/10000)=0)-(ʟBFS>5)(fPart(ʟBFN/100000)=0)→ʟBFN
(ʟBFQ≥10 or ʟBFQ≤⁻4)→ʟBFZ
(ʟBFT<0)+ʟBFZ*(ʟBFN+(ʟBFN>1)+2+(ʟBFQ<0)+(abs(ʟBFQ)≥10))+not(ʟBFZ)*((ʟBFQ≥0)*(max(ʟBFQ+1,ʟBFN)+(ʟBFN>ʟBFQ+1))+(ʟBFQ<0)*(ʟBFN-ʟBFQ))→ʟBFZ
max(1,ʟBFS-(ʟBFZ>ʟBFW)*max(1,ʟBFZ-ʟBFW))→ʟBFS
End
If ʟBFM(1)
Output(1,ʟBFE(1)-ʟBFZ(1)+1,ʟBFT(1))
If ʟBFM(2)
Output(2,ʟBFE(2)-ʟBFZ(2)+1,ʟBFT(2))
If ʟBFM(3)
Output(3,ʟBFE(3)-ʟBFZ(3)+1,ʟBFT(3))
If ʟBFM(4)
Output(4,ʟBFE(4)-ʟBFZ(4)+1,ʟBFT(4))
If ʟBFM(5)
Output(5,ʟBFE(5)-ʟBFZ(5)+1,ʟBFT(5))
If ʟBFM(6)
Output(6,ʟBFE(6)-ʟBFZ(6)+1,ʟBFT(6))
If ʟBFM(7)
Output(7,ʟBFE(7)-ʟBFZ(7)+1,ʟBFT(7))
If ʟBFM(8)
Output(8,ʟBFE(8)-ʟBFZ(8)+1,ʟBFT(8))
If ʟBK(2)<ʟBK(3)
Pause :ʟBK(2)+1→ʟBK(2)
End
DelVar ʟBFV:DelVar ʟBFW:DelVar ʟBFE:DelVar ʟBFM:DelVar ʟBFS
DelVar ʟBFT:DelVar ʟBFQ:DelVar ʟBFN:DelVar ʟBFZ:DelVar ʟBK:DelVar ʟBT
""
