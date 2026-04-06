'''
Related Figures:1
'''
import numpy as np
import scipy.io
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.fftpack import fft

q=mpl.cm.get_cmap("viridis", 3)
c_list=q(range(3))

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
    spike_mean=scipy.io.loadmat('E:/笔迹拟合/dataset/spike/sorted_unit_wf-137.mat')['sorted_unit_wf'].T
    for i in spike_mean:
        plt.plot(np.arange(46)/30,i,linewidth=0.3)
    ax=plt.gca()
    ax.spines['top'].set_color('red')
    ax.spines['right'].set_color('red')
    ax.spines['bottom'].set_color('red')
    ax.spines['left'].set_color('red')
    ax.spines['bottom'].set_linewidth(0.25)
    ax.spines['left'].set_linewidth(0.25)
    ax.spines['top'].set_linewidth(0.25)
    ax.spines['right'].set_linewidth(0.25)
    plt.ylim(-150,150)
    plt.xlabel('Time(ms)')
    plt.ylabel('Amplitude(uv)')
    plt.tick_params(width=0.25, color='red', labelcolor='black')
    plt.show()
    plt.close()
    for i in spike_mean:
        x,y=fft_show(i,30000,zeros_fill=1000,show=False)
        plt.plot(x,y,linewidth=0.3)
    plt.xlabel('Frequency/Hz')
    plt.ylabel('Amplitude/uv')
    plt.xlim(0,3000)
    ax=plt.gca()
    ax.spines['top'].set_color('red')
    ax.spines['right'].set_color('red')
    ax.spines['bottom'].set_color('red')
    ax.spines['left'].set_color('red')
    ax.spines['bottom'].set_linewidth(0.25)
    ax.spines['left'].set_linewidth(0.25)
    ax.spines['top'].set_linewidth(0.25)
    ax.spines['right'].set_linewidth(0.25)
    plt.ylim(0,80)
    plt.xlabel('Time/ms')
    plt.ylabel('Amplitude/uv')
    plt.tick_params(width=0.25, color='red', labelcolor='black')
    plt.show()
    plt.close()
    peak=[]
    
    low=[]
    
    high=[]
    for i in spike_mean:
        x,y=fft_show(i,30000,zeros_fill=1000,show=False)
        ym=y.max()
        xm=x[y.argmax()]
        peak.append(xm)
        thres=ym/2**0.5
        xl=np.where((y<=thres)*(x<xm))[0].max()
        low.append(x[xl])
        xh=np.where((y<=thres)*(x>xm))[0].min()
        high.append(x[xh])
    plt.hist(peak,bins=x,label='peak',color=c_list[0],linewidth=0.3)
    plt.axvline(np.median(np.array(peak)),color='black',linestyle='--',linewidth=0.5)
    plt.hist(low,bins=x,label='low',color=c_list[1],linewidth=0.3)
    plt.axvline(np.median(np.array(low)),color='black',linestyle='--',linewidth=0.5)
    plt.hist(high,bins=x,label='high',color=c_list[2],linewidth=0.3)
    plt.axvline(np.median(np.array(high)),color='black',linestyle='--',linewidth=0.5)
    plt.legend()
    plt.xlim(0,2500)
    ax=plt.gca()
    ax.spines['top'].set_color('red')
    ax.spines['right'].set_color('red')
    ax.spines['bottom'].set_color('red')
    ax.spines['left'].set_color('red')
    ax.spines['bottom'].set_linewidth(0.25)
    ax.spines['left'].set_linewidth(0.25)
    ax.spines['top'].set_linewidth(0.25)
    ax.spines['right'].set_linewidth(0.25)
    plt.ylim(0,30)
    plt.tick_params(width=0.25, color='red', labelcolor='black')
    plt.show()
    plt.close()
    print(np.median(np.array(low)),np.median(np.array(peak)),np.median(np.array(high)))
    
    mean=np.zeros(spike_mean.shape[1])
    for i in spike_mean:
        mean+=i/i.var()**0.5
    mean=mean/spike_mean.shape[0]
    plt.plot(np.arange(20,66)/30,mean,color='red',label='Handwriting',linewidth=0.3)
    plt.legend()
    ax=plt.gca()
    ax.spines['bottom'].set_linewidth(0.25)
    ax.spines['left'].set_linewidth(0.25)
    ax.spines['top'].set_linewidth(0.25)
    ax.spines['right'].set_linewidth(0.25)
    plt.xlabel('Time/ms')
    plt.show()
    plt.close()
    
    mean=np.zeros(500)
    for i in spike_mean:
        x,y=fft_show(i,30000,zeros_fill=1000,show=False)
        mean+=y/y.var()**0.5
    mean=mean/spike_mean.shape[0]
    mean1=mean.copy()
    x1=x.copy()
    plt.plot(x,mean,color='red',label='Handwriting',linewidth=0.3)
    plt.legend()
    plt.show()
    plt.close()