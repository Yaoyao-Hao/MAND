clc
clear all
Q_N = 23;
Q = 2^23-1;%%量化位宽，整数8位小数23位

Q_FIL = Q;
 data = readNPY('D:\YCB\YCB\PROJECT\EEG_signal_processing\python\raw_signal.npy');
 data_Q = floor(data.*Q);
 %ese
 a0 =[ 1.         -0.93906251];
 b0 =[ 0.96953125 -0.96953125];
 a0_Q =floor(a0 .*Q_FIL) ;
 b0_Q =floor(b0 .*Q_FIL) ;
 x_filtered_band0   = filter(b0,a0, data);
 x_filtered_band0_Q = filter_iir_Q(data_Q,a0_Q,b0_Q,2,Q_N);
 x_filtered_band_abs = abs(x_filtered_band0);
 x_filtered_band_abs_Q = abs(x_filtered_band0_Q);
 a1 = [ 1.         -0.99748988];
 b1 = [0.00125506  0.00125506];
 a1_Q =floor(a1 .*Q_FIL) ;
 b1_Q =floor(b1 .*Q_FIL) ;
 x_filtered_band1 = filter(b1,a1, x_filtered_band_abs);
 x_filtered_band1_Q = filter_iir_Q(x_filtered_band_abs_Q,a1_Q,b1_Q,2,Q_N);
 downsampled_signa1 = x_filtered_band1(1:30:end);
 downsampled_signa1_Q = x_filtered_band1_Q(1:30:end);
 mean_win_size = 256;
 npone = zeros(mean_win_size,1);
 npone = npone+1/mean_win_size;
 esa = conv(downsampled_signa1,npone);

 for i = 1:size(downsampled_signa1_Q,1)-mean_win_size
     esa_Q_ave(i) =mean( downsampled_signa1_Q(i:i+mean_win_size-1),1);
 end
 esa_Q_ave= (esa_Q_ave./Q_FIL).';
 esa_Q_out = esa_Q_ave(1:50:end);
 esa_out = esa(mean_win_size:50:end);
 esa_py = readNPY('D:\YCB\YCB\PROJECT\EEG_signal_processing\python\ESA_256Hz.npy');
 esa_py_50 = esa_py(129:50:end);
 delta_esa = esa_Q_out(1:195) - esa_py_50(1:195);
 esa_fpga = load('fpga_cal_data_esa.txt');
 esa_fpga = esa_fpga./Q_FIL;
 esa_fpga = esa_fpga(256:50:end);
  esa_mse = mean((esa_fpga(1:195) - esa_py_50(1:195)).^2);
 figure(1)
 plot(esa_Q_out(1:195), 'r-');   % 红色实线，表示第一个曲线
 hold on;             % 保持当前图形
 plot(esa_py_50(1:195), 'b--');  % 蓝色虚线，表示第二个曲线
 plot(esa_fpga(1:195), 'g-.');  % 绿色点划线，表示第三个曲线
legend('ESA-matlab', 'ESA-python', 'ESA-fpga'); % 添加图例
title({'ESA ';' MSE_e_s_a:'},num2str(esa_mse));

 %SBP
 a2 = [ 1.         -3.76832677  5.35202538  -3.39629194  0.81274967];
 b2 = [ 0.00486164  0.         -0.00972329  0.          0.00486164];
 a2_Q =floor(a2 .*Q_FIL) ;
 b2_Q =floor(b2 .*Q_FIL) ;
 SBP0 = filter(b2,a2, data);
 SBP0a = filter_iir(data,a2,b2,5);
 SBP0_Q = filter_iir_Q(data_Q,a2_Q,b2_Q,5,Q_N);
 SBP_ABS = abs(SBP0);
 SBP_ABS_Q = abs(SBP0_Q);
 downsampled_sbp   = SBP_ABS(1:15:end)  ;
 downsampled_sbp_Q = SBP_ABS_Q(1:15:end);
 mean_win_size = 512;
 npone = zeros(mean_win_size,1);
 npone = npone+1/mean_win_size;
 SBP = conv(downsampled_sbp,npone);
  for i = 1:size(downsampled_sbp_Q,1)-mean_win_size
     SBP_Q_ave(i) =mean( downsampled_sbp_Q(i:i+mean_win_size-1),1);
  end
  SBP_py = readNPY('D:\YCB\YCB\PROJECT\EEG_signal_processing\python\SBP_256Hz.npy');
  SBP_py_100 = SBP_py(257:100:end);
  SBP_Q_ave= (SBP_Q_ave./Q_FIL).';
  SBP_Q_OUT= SBP_Q_ave(1:100:end);
  
 SBP_fpga = load('fpga_cal_data_sbp.txt');
 SBP_fpga = SBP_fpga./Q_FIL;
 SBP_fpga = SBP_fpga(257+256:100:end);
 SBP_mse = mean((SBP_fpga(1:195)-SBP_py_100(1:195)).^2);
 figure(2)
 plot(SBP_Q_OUT(1:195), 'r-');   % 红色实线，表示第一个曲线
 hold on;             % 保持当前图形
 plot(SBP_py_100(1:195), 'b--');  % 蓝色虚线，表示第二个曲线
 plot(SBP_fpga(1:195), 'g-.');  % 绿色点划线，表示第三个曲线
legend('SBP-matlab', 'SBP-python', 'SBP-fpga'); % 添加图例
title({'SBP ';' SBP_e_s_a:'},num2str(SBP_mse));

%   SBP_py = readNPY('D:\YCB\YCB\PROJECT\EEG_signal_processing\python\SBP_200hz.npy');
  SBP_OUT = SBP(400:100:end);
  delta_sbp = SBP_Q_OUT(1:195)-SBP_py(1:195);
  
%MAND
MAND = data;
MAND_Q = data_Q;
mean_win_size = 4096;
a = size(data,1);
for i = 16:a
MAND(i)= MAND(i) -  data(i-15);
MAND_Q(i) = MAND_Q(i) - data_Q(i-15);
end
MAND_abs = abs(MAND);
MAND_abs_Q = abs(MAND_Q);
 npone = zeros(mean_win_size,1);
 npone = npone+1/mean_win_size;
MAND_conv = conv(MAND_abs,npone);
MAND_OUT = MAND_conv(mean_win_size:1500:end);

  for i = 1:size(MAND_abs_Q,1)-mean_win_size
     MAND_Q_ave(i) =mean( MAND_abs_Q(i:i+mean_win_size-1),1);
  end
  MAND_Q_ave = (MAND_Q_ave).'./Q;
  MAND_Q_out = MAND_Q_ave(1:1024:end);
   MAND_py = readNPY('D:\YCB\YCB\PROJECT\EEG_signal_processing\python\MAND_200hz.npy');
   MAND_py_d = MAND_py./6000;
 mandzish = readNPY('D:\YCB\YCB\PROJECT\EEG_signal_processing\python\mandzish.npy');
 mandzish_fpga = load('fpga_cal_data_MAN.txt')./Q;
 mandzish      = mandzish(2049:1024:end);
  MAND_mse = mean((mandzish_fpga(4:198) - mandzish(1:195)).^2);
  figure(3)
 plot(MAND_Q_out(1:195), 'r-');   % 红色实线，表示第一个曲线
 hold on;             % 保持当前图形
 plot(mandzish(1:195), 'b--');  % 蓝色虚线，表示第二个曲线
 plot(mandzish_fpga(4:198), 'g-.');  % 绿色点划线，表示第三个曲线
legend('MAND-matlab', 'MAND-python', 'MAND-fpga'); % 添加图例
title({'MAND ';' MAND_e_s_a:'},num2str(MAND_mse));
 
 
 %优化算法
 

 delta_MAND = MAND_Q_out(1:195) - MAND_py_d(1:195);
%  disp(['esa_mse: ', num2str(esa_mse)]);
%  disp(['SBP_mse: ', num2str(SBP_mse)]);
%  disp(['MAND_mse: ', num2str(MAND_mse)]);
%  figure(1)
%  subplot(3,1,1)
%  plot(delta_esa);title('ESA mse:  ', num2str(esa_mse));
%  subplot(3,1,2)
%  plot(delta_sbp);title('SBP mse:  ',num2str(SBP_mse));
%  subplot(3,1,3)
%  plot(delta_MAND);title('MAND mse:  ',num2str(MAND_mse));
 
 
 fid = fopen('data_Q.txt','wt');
 for i = 1:size(data_Q,1)
  fprintf(fid,'%d\n',data_Q(i));
 end
fclose(fid);