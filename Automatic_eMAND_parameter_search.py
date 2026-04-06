"""
Related Figures:
"""

import numpy as np
import scipy
import scipy.io
from scipy.fftpack import fft

def get_fft(sequence,sf,zeros_fill=None):
    '''
    频率图绘制
    输入为一维numpy数组（时序），
         采样频率（sampling frequency），
    输出为原信号图和对应的信号频率图
    '''
    N=sequence.reshape(-1).shape[0]
    if zeros_fill==None:
        sequence1=sequence.reshape(-1)
    else:
        sequence1=np.zeros(zeros_fill)
        sequence1[:sequence.reshape(-1).shape[0]]=sequence.reshape(-1)
    n=len(sequence1)
    t=np.arange(0,(n-0.5)/sf,1/sf)
    # print(n,N)
    fft_data=fft(sequence1)
    fft_amp0 = np.array(np.abs(fft_data)/n*2)   # 用于计算双边谱
    fft_amp0[0]=0.5*fft_amp0[0]
    n_2 = int(n/2)
    
    fft_amp1 = fft_amp0[0:n_2]  # 单边谱
    if zeros_fill!=None:
        fft_amp1=fft_amp1/N*n
    
    # 计算频谱的频率轴
    list1 = np.array(range(0, int(n/2)))
    freq1 = sf/n*list1        # 单边谱的频率轴
    return freq1,fft_amp1

if __name__=="__main__":
    spikes=scipy.io.loadmat('sorted_unit_wf_path')
    mean_spike_spectrum=np.zeros(500)
    for i in spikes:
        x,y=get_fft(i,30000,zeros_fill=1000)
        mean_spike_spectrum+=y
    mean_spike_spectrum=mean_spike_spectrum/spikes.shape[0]
    
    n_list=[i for i in range(11,21)]
    w_list=[i/10 for i in range(-10,11)]
    k_list=[i for i in range(7,38)]
    mean_spike_spectrum=mean_spike_spectrum/mean_spike_spectrum.max()
    parameter_set_list=[]
    similarity_list=[]
    for i in range(10):
        for j in range(21):
            for m in range(31):
                n=n_list[i]
                w=w_list[j]
                k=k_list[m]
                b=np.zeros(100)
                b[0]=(1+w)
                b[n]+=-1
                b[k]+=-w
                f,amp=scipy.signal.freqz(b, worN=1000, whole=True, fs=30000)
                amp=np.abs(amp)[:500]
                amp[1:]=amp[1:]/f[1:]
                first_peak=amp[scipy.signal.find_peaks(amp)[0][0]]
                amp=amp/first_peak
                parameter_set_list.append([n,w,k])
                similarity=((amp-mean_spike_spectrum)**2).mean()
                similarity_list.append(similarity)
    best_parameter_set=parameter_set_list[np.array(similarity_list).argmin()]