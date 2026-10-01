ClrHome
Disp "MATRIX TRACE"
Input "WHICH [A]-[J]? ",Str1
0→N
If length(Str1)=1
inString("ABCDEFGHIJ",Str1)→N
If not(N)
Then
Disp "NAME MUST BE A-J"
Stop
End
If N=1:Then:dim([A])→L₆:sum(seq([A](I,I),I,1,min(L₆)))→T:End
If N=2:Then:dim([B])→L₆:sum(seq([B](I,I),I,1,min(L₆)))→T:End
If N=3:Then:dim([C])→L₆:sum(seq([C](I,I),I,1,min(L₆)))→T:End
If N=4:Then:dim([D])→L₆:sum(seq([D](I,I),I,1,min(L₆)))→T:End
If N=5:Then:dim([E])→L₆:sum(seq([E](I,I),I,1,min(L₆)))→T:End
If N=6:Then:dim([F])→L₆:sum(seq([F](I,I),I,1,min(L₆)))→T:End
If N=7:Then:dim([G])→L₆:sum(seq([G](I,I),I,1,min(L₆)))→T:End
If N=8:Then:dim([H])→L₆:sum(seq([H](I,I),I,1,min(L₆)))→T:End
If N=9:Then:dim([I])→L₆:sum(seq([I](I,I),I,1,min(L₆)))→T:End
If N=10:Then:dim([J])→L₆:sum(seq([J](I,I),I,1,min(L₆)))→T:End
If L₆(1)≠L₆(2)
Then
Disp "NOT SQUARE"
Stop
End
Disp "TRACE:",T
