%this is REALLY slow (300-400 ms on average)
function inter = sol(pos, vel, rad, offset)
    t = cputime;
    syms f(x) g(x);
    
    m = vel(2)/vel(1); %determine slope
    b = pos(2) - m*pos(1); %determine intercept
    f(x) = piecewise(-1.9<x<-1.7, m*x + b); %define line segment
    g(x) = piecewise(-3.3<x<-1, sqrt(rad - (x + offset)^2)); %define arc
    
    %solve the equations, and check for intercept
    try
        solve(f == g);
        inter = 1;
    catch
        inter = 0;
    end
    
    disp(cputime - t)
    
    %[x,y] = solve(f(x), g(x))
    
    %t = -3.3:0.1:-1;
    %plot(t, g(t))
    
    %hold on;
    
    %t2 = -1.9:0.02:-1.7;
    %plot(t2, f(t2))
end