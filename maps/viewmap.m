clc;
mapData = jsondecode(fileread('./markerdata/map1.json'));
fields = fieldnames(mapData);

ix = mapData.inner.x.';
iy = mapData.inner.y.';
ox = mapData.outer.x.';
oy = mapData.outer.y.';

x = [-1.789575 -2.034244 -2.281847 -2.509147 ...
     -2.746005 -2.935855 -3.029079 -3.014436 ...
     -2.891111 -2.699403 -2.445857 -2.135631 ...
     -1.788770];

y = [1.23981 1.216462 1.131472 1.003406 ...
     0.791122 0.488427 0.124798 -0.204538 ...
     -0.565247 -0.836731 -1.047305 -1.181101 ...
     -1.229271];
 
%car vector
%x2 = [-1.8 -2];
%y2 = [1 1.1];
p = [-1.8; 1];
r = [-0.2; 0.1];

xinters = [];
yinters = [];
figure(1);
hold on;
plot([p(1) p(1)+r(1)], [p(2) p(2)+r(2)], 'r-')

for k = 1:numel(fields)
    for i = 2:length(mapData.(fields{k}).x)
        disp(mapData.(fields{k}).x)
        tx = [mapData.(fields{k}).x(i-1) mapData.(fields{k}).x(i)];
        ty = [mapData.(fields{k}).y(i-1) mapData.(fields{k}).y(i)];
        plot(tx, ty, 'b-');

        q = [tx(1); ty(1)];
        s = [tx(2) - tx(1); ty(2) - ty(1)];

        t = (det(cat(2,(q - p), s)))*inv(det(cat(2, r, s)));
        u = (det(cat(2,(q - p), r)))*inv(det(cat(2, r, s)));

        if(t >= 0 && t <= 1 && u >= 0 && u <= 1)
            int = p + t*r;
            disp(int)
            plot(int(1), int(2), 'r*')
        end
    end
end