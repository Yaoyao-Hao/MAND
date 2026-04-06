"""
Related Figures:
"""

from feature_extracting import*
import numyp as np
import colorednoise as cn

if __name__=="__main__":
    neural_signal=np.load('')
    esa=ESA(neural_signal)
    emand=eMAND(neural_signal)
    mua=MUA(neural_signal)
    sbp=SBP(neural_signal)
    cc=np.corrcoef(emand,sbp)[0,1]
    white_noise_cc=np.ones((4,7))
    pink_noise_cc=np.ones((4,7))
    for i in range(1,7):
        data_with_noise=neural_signal+i*0.05*neural_signal.std()*cn.powerlaw_psd_gaussian(1, neural_signal.shape[0])
        esa_with_noise=ESA(data_with_noise)
        emand_with_noise=eMAND(data_with_noise)
        mua_with_noise=MUA(data_with_noise)
        sbp_with_noise=SBP(data_with_noise)
        pink_noise_cc[0,i]=np.corrcoef(emand_with_noise,emand)[0,1]
        pink_noise_cc[1,i]=np.corrcoef(esa_with_noise,esa)[0,1]
        pink_noise_cc[2,i]=np.corrcoef(sbp_with_noise,sbp)[0,1]
        pink_noise_cc[3,i]=np.corrcoef(mua_with_noise,mua)[0,1]
    for i in range(1,7):
        data_with_noise=neural_signal+i*0.05*neural_signal.std()*np.random.randn(neural_signal.shape[0])
        esa_with_noise=ESA(data_with_noise)
        emand_with_noise=eMAND(data_with_noise)
        mua_with_noise=MUA(data_with_noise)
        sbp_with_noise=SBP(data_with_noise)
        white_noise_cc[0,i]=np.corrcoef(emand_with_noise,emand)[0,1]
        white_noise_cc[1,i]=np.corrcoef(esa_with_noise,esa)[0,1]
        white_noise_cc[2,i]=np.corrcoef(sbp_with_noise,sbp)[0,1]
        white_noise_cc[3,i]=np.corrcoef(mua_with_noise,mua)[0,1]