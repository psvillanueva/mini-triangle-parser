let 
var x: Integer;
var y: Integer;
var z: Integer;
in
begin
getint(x);
getint(y);
z := x+x*y;
putint(z);
z := x*y+x;
putint(z);
z := x+x*y = x*y+x;
putint(z);
end