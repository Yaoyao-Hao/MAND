function y = filter_iir(x,a,b,N)
size_x = size(x,1);  
y = x;
w_a = 0;
w_b = 0;
N = N;
for i = 1:N
   for j = 1: i
     w_a = b(j) * x(i-(j-1)) + w_a; 
   end
   if(i == 1) 
    w_b = 0;
   else   
    for j = 2: i
      w_b = a(j) * y(i-(j-1)) + w_b;  
    end 
   end
    y(i) = w_a - w_b;
    w_b = 0;
    w_a = 0;
end



for i =N + 1 : size_x - N
   for j = 1: N 
     w_a = b(j) * x(i-(j-1)) + w_a; 
   end   
    for j = 2 : N
     w_b = a(j ) * y(i-(j-1)) + w_b;  
    end  
    y(i) = w_a - w_b;
    w_b = 0;
    w_a = 0;
end
end