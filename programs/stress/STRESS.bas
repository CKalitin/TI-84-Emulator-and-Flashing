ClrHome
Input "MATRIX A-J? ",Str1
{0}→ʟSIG:ClrList ʟSIG
If Str1="A":Then:dim([A])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([A](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If Str1="B":Then:dim([B])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([B](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If Str1="C":Then:dim([C])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([C](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If Str1="D":Then:dim([D])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([D](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If Str1="E":Then:dim([E])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([E](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If Str1="F":Then:dim([F])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([F](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If Str1="G":Then:dim([G])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([G](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If Str1="H":Then:dim([H])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([H](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If Str1="I":Then:dim([I])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([I](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If Str1="J":Then:dim([J])→ʟSIG:If ʟSIG(1)=ʟSIG(2):augment({ʟSIG(1)},seq([J](iPart((K-1)/ʟSIG(1))+1,K-ʟSIG(1)iPart((K-1)/ʟSIG(1))),K,1,ʟSIG(1)²))→ʟSIG:End
If not(dim(ʟSIG))
Then
Disp "NAME MUST BE A-J"
Stop
End
If dim(ʟSIG)≠ʟSIG(1)²+1
Then
Disp "NOT SQUARE"
Stop
End
If ʟSIG(1)≠2 and ʟSIG(1)≠3
Then
Disp "NEED 2X2 OR 3X3"
Stop
End
If ʟSIG(1)=2
Then
{ʟSIG(2),ʟSIG(5),0,ʟSIG(3),0,0,ʟSIG(3)=ʟSIG(4)}→ʟSIG
Else
{ʟSIG(2),ʟSIG(6),ʟSIG(10),ʟSIG(3),ʟSIG(7),ʟSIG(4),ʟSIG(3)=ʟSIG(5) and ʟSIG(4)=ʟSIG(8) and ʟSIG(7)=ʟSIG(9)}→ʟSIG
End
If not(ʟSIG(7))
Then
Disp "NOT SYMMETRIC"
Stop
End
6→dim(ʟSIG)
{ʟSIG(1)+ʟSIG(2)+ʟSIG(3),ʟSIG(1)ʟSIG(2)+ʟSIG(2)ʟSIG(3)+ʟSIG(3)ʟSIG(1)-ʟSIG(4)²-ʟSIG(5)²-ʟSIG(6)²,ʟSIG(1)ʟSIG(2)ʟSIG(3)+2ʟSIG(4)ʟSIG(5)ʟSIG(6)-ʟSIG(1)ʟSIG(5)²-ʟSIG(2)ʟSIG(6)²-ʟSIG(3)ʟSIG(4)²,((ʟSIG(1)-ʟSIG(2))²+(ʟSIG(2)-ʟSIG(3))²+(ʟSIG(3)-ʟSIG(1))²)/6+ʟSIG(4)²+ʟSIG(5)²+ʟSIG(6)²}→ʟINV
augment({ʟSIG(1),ʟSIG(2),ʟSIG(3)}-ʟINV(1)/3,{ʟSIG(4),ʟSIG(5),ʟSIG(6),max(abs(ʟSIG))})→ʟSIG
augment(ʟINV,{ʟSIG(1)ʟSIG(2)ʟSIG(3)+2ʟSIG(4)ʟSIG(5)ʟSIG(6)-ʟSIG(1)ʟSIG(5)²-ʟSIG(2)ʟSIG(6)²-ʟSIG(3)ʟSIG(4)²})→ʟINV
ʟINV*(abs(ʟINV)≥10^(⁻12)ʟSIG(7)^{1,2,3,2,3})→ʟINV
augment(ʟINV,{√(3ʟINV(4))})→ʟINV
round(ʟINV/10^int(log(abs(ʟINV)+not(ʟINV))),5)10^int(log(abs(ʟINV)+not(ʟINV)))→ʟSIG
ClrHome
Output(1,1,"STRESS ["+Str1+"]")
Output(3,1,"I_1=")
Output(4,1,"I_2=")
Output(5,1,"I_3=")
Output(6,1,"J_2=")
Output(7,1,"J_3=")
Output(8,1,"σ_vM=")
Output(3,5,ʟSIG(1))
Output(4,5,ʟSIG(2))
Output(5,5,ʟSIG(3))
Output(6,5,ʟSIG(4))
Output(7,5,ʟSIG(5))
Output(8,6,ʟSIG(6))
""
