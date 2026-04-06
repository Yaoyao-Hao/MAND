'''
Related Figures:2c-f,2g,2i,s3,s4
'''
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
from scipy.fftpack import fft

def wave_filter(sequence,cof,sf,mod,N=4):
    if len(sequence.shape)==1:
        sequence=sequence.reshape(1,-1)
    b, a = signal.butter(N, cof, btype=mod,fs=sf)
    filtedData = signal.filtfilt(b, a, sequence)
    return filtedData

def ESA(signal):
    intermediate1=wave_filter(signal,300,30000,'highpass',1)[0]
    intermediate2=np.abs(intermediate1)
    feature=wave_filter(intermediate2,12,30000,'lowpass',1)[0]
    return intermediate1,intermediate2,feature[::30]

def SBP(signal):
    intermediate1=wave_filter(signal,[300,1000],30000,'bandpass',2)[0]
    feature=np.abs(intermediate1)
    return intermediate1,feature[::15]

def MUA(signal):
    feature=wave_filter(signal,[250,5000],30000,'bandpass',4)[0]
    rms = np.sqrt(np.mean(np.square(feature)))
    tmp = (feature>(-4.5*rms)).astype(np.int64)
    feature=(np.diff(tmp)==1)
    return feature

def eMAND(signal,n=11,w=0,k=30):
    intermediate1=signal.copy()
    intermediate1[n+k:]=signal[n+k:]-signal[k:-n]+w*(signal[n+k:]-signal[n:-k])
    feature=np.abs(intermediate1)
    return intermediate1,feature

def fft_show(sequence,sf,zeros_fill=None,xlog=False,ylog=False,xlim=None,ylim=None,show=True,save_path=None):
    N=sequence.reshape(-1).shape[0]
    if zeros_fill==None:
        sequence1=sequence.reshape(-1)
    else:
        sequence1=np.zeros(zeros_fill)
        sequence1[:sequence.reshape(-1).shape[0]]=sequence.reshape(-1)
    n=len(sequence1)
    t=np.arange(0,(n-0.5)/sf,1/sf)
    fft_data=fft(sequence1)
    fft_amp0 = np.array(np.abs(fft_data)/n*2)
    fft_amp0[0]=0.5*fft_amp0[0]
    n_2 = int(n/2)
    
    fft_amp1 = fft_amp0[0:n_2]
    if zeros_fill!=None:
        fft_amp1=fft_amp1/N*n
    
    list1 = np.array(range(0, int(n/2)))
    freq1 = sf/n*list1
    if show:
        plt.figure(dpi=300,constrained_layout=True)
        plt.subplot(211)
        plt.plot(t, sequence1)
        plt.title(' Original signal')
        plt.xlabel('t (s)')
        plt.ylabel(' Amplitude ')
        plt.subplot(212)
        plt.plot(freq1, fft_amp1)
        plt.title(' spectrum single-sided')
        plt.xlabel('frequency  (Hz)')
        plt.ylabel(' Amplitude ')
        if xlog:
            plt.xscale("log")
        if ylog:
            plt.yscale("log")
        if xlim!=None:
            plt.xlim(xlim[0],xlim[1])
        if ylim!=None:
            plt.ylim(ylim[0],ylim[1])
        if save_path!=None:
            plt.savefig(save_path, dpi=300)
        plt.show()
        plt.close()
    return freq1,fft_amp1

if __name__ == "__main__":
    #Intermediate signal amplitude spectrum during feature extraction
    raw_signal=np.load('')
    t=1500000
    signal_segment=raw_signal[t:t+300000]
    fft_show(signal_segment, 30000)
    intermediate_feature=eMAND(signal_segment)
    for i in intermediate_feature:
        fft_show(i, 30000)