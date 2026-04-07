# -*- coding: utf-8 -*-
"""
Created on Thu Apr 17 15:12:02 2025

@author: 24233
"""

import numpy as np
import scipy.signal as signal
from scipy.io import savemat
from array import array



def ESA(raw_signal):
    b, a = signal.butter(1, 300, btype='highpass',fs=30000)
    filted_signal_1 = signal.lfilter(b, a, raw_signal)
    abs_signal=np.abs(filted_signal_1)
    b,a=signal.butter(1, 12, btype='lowpass',fs=30000)
    filted_signal_2 = signal.lfilter(b, a, abs_signal)
    downsampled_signal=filted_signal_2[::30]
    a1 = np.ones(256)/256
    esa_out=np.convolve(downsampled_signal, np.ones(256)/256,mode='same')
    esa=esa_out[::50]
    return esa_out,filted_signal_2,esa

def SBP(raw_signal):
    b, a = signal.butter(2, [300,1000], btype='bandpass',fs=30000)
    filted_signal_1 = signal.lfilter(b, a, raw_signal)
    abs_signal=np.abs(filted_signal_1)
    downsampled_signal=abs_signal[::15]
    sbp_out=np.convolve(downsampled_signal, np.ones(512)/512,mode='same')
    sbp = sbp_out[::100]
    return sbp_out,abs_signal,sbp

def MAND(raw_signal):
    differential_signal = raw_signal.copy()
    differential_signal[15:]=differential_signal[15:]-differential_signal[:-15]
    abs_signal=np.abs(differential_signal)
    np.save('abs_signal.npy', abs_signal)
    a = np.ones(6000)
    mandzish=np.convolve(abs_signal, np.ones(4096)/4096,mode='same')
    np.save('mandzish.npy', mandzish)
    mandzish = mandzish[::1500]
    return abs_signal,mandzish

def MUA(raw_signal,rms=21.25704080830074):
    threshold=-4.5*rms
    at=time.time_ns()
    b, a = signal.butter(4, [250,5000], btype='bandpass',fs=30000)
    filted_signal = signal.lfilter(b, a, raw_signal)
    tmp = (filted_signal>(threshold)).astype(np.int64)
    tmp[1:] = tmp[1:]-tmp[:-1]
    spike=(tmp==1).astype(np.int64)
    bt=time.time_ns()
    bined_spike=spike.reshape(-1,1500).sum(1)
    bined_spike=np.convolve(bined_spike, np.ones(4),mode='same')
    ct=time.time_ns()
    return bined_spike
    #return (bt-at),(ct-at),spike,bined_spike


raw_signal = np.load('raw_signal.npy')
[esa_out,filted_signal_2,esa] =ESA(raw_signal)
[sbp_out,filted_signal_3,sbp] =SBP(raw_signal)
[filted_signal_4,MAND] =MAND(raw_signal)
[mua_out] =MUA(raw_signal)
print(raw_signal)
np.save('MAND.npy',MAND)
np.save('ESA_256Hz.npy',esa_out)
np.save('SBP_256Hz.npy',sbp_out)
np.save('mua_out.npy',mua_out)