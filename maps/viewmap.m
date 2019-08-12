clc;
mapData = jsondecode(fileread('./markerdata/map1.json'));

ix = mapData.inner.x.';
iy = mapData.inner.y.';
ox = mapData.outer.x.';
oy = mapData.outer.y.';

i = [ix; iy];
o = [ox; oy];

map = {i;o};
 
%car vector
%x2 = [-1.8 -2];
%y2 = [1 1.1];
p = [-1.7; 1.4];
r = [-0.2; 0.3];

xinters = [];
yinters = [];

clf;
figure(1);
hold on;
plot([p(1) p(1)+r(1)], [p(2) p(2)+r(2)], 'r-')
hold on;

t1x = -3.3:0.1:-2;
t1y = sqrt(2.2 - (t1x + 1.8).^2);

plot(t1x, t1y)
plot(t1x, -t1y)

for k = 1:size(map, 1)
    for i = 2:size(map{k}, 2)
        tx = [map{k}(1, i-1) map{k}(1, i)]; %[mapData.(fields{k}).x(i-1) mapData.(fields{k}).x(i)];
        ty = [map{k}(2, i-1) map{k}(2, i)];
        plot(tx, ty, 'b-');

        q = [tx(1); ty(1)];
        s = [tx(2) - tx(1); ty(2) - ty(1)];

        t = (det(cat(2,(q - p), s)))*inv(det(cat(2, r, s)));
        u = (det(cat(2,(q - p), r)))*inv(det(cat(2, r, s)));

        if(t >= 0 && t <= 1 && u >= 0 && u <= 1)
            int = p + t*r;
            plot(int(1), int(2), 'r*')
        end
    end
end

function [x,y] = solve(pos, vel, rad, offset)
    syms f(x) g(x);
    
    m = vel(2)/vel(1); %determine slope
    b = pos(2) - m*pos(1); %determine intercept
    
    f(x) = piecewise(-1.9<x<-1.7, m*x + b); %define line segment
end
