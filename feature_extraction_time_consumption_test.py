'''
Related Figures:5a
'''
import time
import numpy as np
import scipy.signal as signal

def wave_filter(sequence,cof,sf,mod,N=4):
    if len(sequence.shape)==1:
        sequence=sequence.reshape(1,-1)
    b, a = signal.butter(N, cof, btype=mod,fs=sf)
    filtedData = signal.filtfilt(b, a, sequence)
    return filtedData

def ESA(signal):
    intermediate1=wave_filter(signal,300,30000,'highpass',1)[0]
    intermediate2=np.abs(intermediate1)
    feature=wave_filter(intermediate2,12,30000,'lowpass',1)[0][::30]
    smooth_feature=np.correlate(feature.reshape(-1,50).mean(1), np.ones(4)/4,mode='same')
    return smooth_feature

def SBP(signal):
    intermediate1=wave_filter(signal,[300,1000],30000,'bandpass',2)[0]
    feature=np.abs(intermediate1)[::15]
    smooth_feature=np.correlate(feature.reshape(-1,100).mean(1), np.ones(4)/4,mode='same')
    return smooth_feature

def eMAND(signal,n=11,w=0,k=30):
    intermediate1=signal.copy()
    intermediate1[n+k:]=signal[n+k:]-signal[k:-n]+w*(signal[n+k:]-signal[n:-k])
    feature=np.abs(intermediate1)
    smooth_feature=np.correlate(feature.reshape(-1,1500).mean(1), np.ones(4)/4,mode='same')
    return smooth_feature

def MUA(signal,rms):
    filted_signal = wave_filter(signal,250,30000,'highpass',2)[0]
    threshold=-4.5*rms
    tmp = (filted_signal>(threshold)).astype(np.int64)
    tmp[1:] = tmp[1:]-tmp[:-1]
    spike=(tmp==1)
    smooth_feature=np.correlate(spike.reshape(-1,1500).sum(1), np.ones(4),mode='same')
    return smooth_feature

if __name__=="__main__":
    neural_signal=np.load('')
    segment_length=1*30000
    time_cost=[]
    for _ in range(1000):
        start=np.random.randint(0,neural_signal.shape[0]-segment_length)
        signal_segment=neural_signal[start:start+segment_length]
        s=time.time_ns()
        ESA(signal_segment)
        e=time.time_ns()
        time_cost.append(e-s)
        