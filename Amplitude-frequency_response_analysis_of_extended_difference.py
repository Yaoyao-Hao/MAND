'''
Related Figures:2a,4,s1
'''
import scipy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

def zplane(z, p, fig=None, ax=None):
    if fig==None or ax==None:
        fig, ax = plt.subplots(figsize=(4, 4),dpi=300)
    circle = Circle(xy = (0.0, 0.0), radius = 1, alpha = 0.9, facecolor = 'white')
    theta = np.linspace(0, 2 * np.pi, 200)
    x = np.cos(theta)
    y = np.sin(theta)
    ax.add_patch(circle)
    ax.plot(x, y, linestyle='--', color='b', linewidth=0.25)
    lim = max(max(z), max(p), 1) + 1
    plt.xlim([-lim, lim])
    plt.ylim([-lim, lim])
    plt.axhline(0, linestyle='--', color='b', linewidth=0.25)
    plt.axvline(0, linestyle='--', color='b', linewidth=0.25)
    for i in z[:-1]:
        ax.scatter(np.real(i),np.imag(i),marker='o',s=10,color='r')
    ax.scatter(np.real(z[-1]),np.imag(z[-1]),marker='o',s=10,color='r',label='Zero')
    for i in p[:1]:
        ax.scatter(np.real(i),np.imag(i),marker='x',s=10,color='r',label='Pole')
    plt.title('Pole-zero plot')
    plt.ylabel('Im(z)')
    plt.xlabel('Re(z)')
    plt.legend()

if __name__ == "__main__":
    fs = 30000
    n=13
    w=-0.6
    k=32
    b=np.zeros(100)
    b[0]=1+w
    b[n]+=-1
    b[k]+=-w
    s, h = scipy.signal.freqz(b)
    plt.subplot(2, 1, 1)
    plt.plot(s * fs / (2 * np.pi), abs(h))
    plt.title('Amplitude-frequency Curve')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Amplitude')
    plt.xlim(0,7500)

    plt.subplot(2, 1, 2)
    plt.plot(s * fs / (2 * np.pi), np.angle(h))
    plt.title('phase-frequency curve')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Phase (rad)')
    plt.xlim(0,7500)

    plt.tight_layout()
    plt.show()
    plt.close()
    a=np.zeros(100)
    a[0]=1
    z,p,k=scipy.signal.tf2zpk(b,a)
    zplane(z,p)
    plt.show()
    plt.close()

    s=scipy.signal.dlti(b,a)
    t,y=scipy.signal.dimpulse(s)
    fig, ax = plt.subplots(dpi=300)
    plt.axhline(0,color='black')
    for i in range(20):
        if y[0][i,0]!=0:
            plt.vlines(t[i],0,np.sign(y[0][i,0])*(np.abs(y[0][i,0])-0.01),color='black')
        ax.scatter(t[i], y[0][i,0],s=10,color='white',edgecolors='black',marker='o',zorder=2)
    plt.grid(linestyle = '--', linewidth = 0.25)
    ax.set_xticks([0,5,10,15,20])
    ax.set_ylim(-1.1,2.1)
    plt.show()
    plt.close()