clc
clear all



 data = readNPY('D:\YCB\YCB\PROJECT\EEG_signal_processing\python\raw_signal.npy');
 %ese
 a0 =[ 1.         -0.93906251];
 b0 =[ 0.96953125 -0.96953125];
 x_filtered_band0 = filter(b0,a0, data);
 x_filtered_band_abs = abs(x_filtered_band0);
 a1 = [ 1.         -0.99748988];
 b1 = [0.00125506  0.00125506];
 x_filtered_band1 = filter(b1,a1, x_filtered_band_abs);
 downsampled_signa1 = x_filtered_band1(1:30:end);
 npone = zeros(200,1);
 npone = npone+1/200;
 esa = conv(downsampled_signa1,npone);
 esa_out = esa(100:50:end);
 
 %SBP
 a2 = [ 1.         -3.76832677  5.35202538 -3.39629194  0.81274967];
 b2 = [ 0.00486164  0.         -0.00972329  0.          0.00486164];
 SBP0 = filter(b2,a2, data);
 SBP_ABS = abs(SBP0);
 downsampled_sbp = SBP_ABS(1:15:end);
 npone = zeros(400,1);
 npone = npone+1/400;
 SBP = conv(downsampled_sbp,npone);
 SBP_OUT = SBP(200:100:end);
 
%MAND
MAND = data;
a = size(data,1);
for i = 16:a
MAND(i)= MAND(i) -  data(i-15);
end
MAND_abs = abs(MAND);
 npone = zeros(6000,1);
 npone = npone+1/6000;
MAND_conv = conv(MAND_abs,npone);
MAND_OUT = MAND_conv(3000:1500:end);
mandzish = readNPY('D:\YCB\YCB\PROJECT\EEG_signal_processing\python\mandzish.npy');

delta = MAND_abs - mandzish;
 