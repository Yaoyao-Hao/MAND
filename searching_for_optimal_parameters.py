'''
Related Figures:4e,s6
'''
import numpy as np
import scipy.io
from kalman_filter import*

def cut(feature_list,mark_list,lists=0):
    '''
    Based on mask segmentation features (temporal sequence)
    '''
    if lists==0:
        start_mark=0
        end_mark=start_mark
        res=[]
        while True:
            start_mark=end_mark
            while True:
                end_mark=end_mark+1
                if end_mark==len(mark_list) or mark_list[start_mark]!=mark_list[end_mark]:
                    break
            res.append(feature_list[:,start_mark:end_mark])
            if end_mark==len(mark_list):
                break
    else:
        start_mark=0
        end_mark=start_mark
        n=len(mark_list)
        m=len(feature_list)
        res=[[] for i in range(m)]
        while True:
            start_mark=end_mark
            while True:
                end_mark=end_mark+1
                if end_mark==n or mark_list[start_mark]!=mark_list[end_mark]:
                    break
            for i in range(m):
                res[i].append(feature_list[i][:,start_mark:end_mark])
            if end_mark==n:
                break
    return res

def get_kalman_result(dataset_list):
    cc = []
    mse = []
    for j,dataset in enumerate(dataset_list):
        target_num=dataset['fold_num'].shape[1]
        trial_num=dataset['trial_mask'].max()
        dataset['bined_spk']=(dataset['bined_spk'].T-dataset['bined_spk'].mean(1)).T
        
        CC = np.zeros((trial_num,2))
        MSE = np.zeros((trial_num,1))
        prediction = [0 for i in range(trial_num)]
        
        for i_target in range(target_num):
            target_ind = np.where(dataset['trial_target']-1 == i_target)[0]
            bins_remove = np.concatenate([np.where(dataset['trial_mask']-1 == target_ind[i])[1] for i in range(len(target_ind))],axis=0)
            trial_velocity_cv=np.delete(dataset['trial_velocity'],bins_remove,axis=1)
            bined_spk_cv=np.delete(dataset['bined_spk'],bins_remove,axis=1)
            
            # single model
            model = kalman_filter(trial_velocity_cv,bined_spk_cv)
            for i_ind in range(len(target_ind)):
                CC[target_ind[i_ind],:],MSE[target_ind[i_ind],0],prediction[target_ind[i_ind]] = model.fit(dataset['trial_velocity'][:,np.where(dataset['trial_mask']-1 == target_ind[i_ind])[1]],dataset['bined_spk'][:,np.where(dataset['trial_mask']-1 == target_ind[i_ind])[1]])
        cc.append(CC)
        mse.append(MSE)
    cc=np.concatenate(cc,axis=0)
    mse=np.concatenate(mse,axis=0)
    return cc,mse

if __name__ == "__main__":
    n_list=[i for i in range(11,21)]
    w_list=[i/10 for i in range(-10,11)]
    k_list=[i for i in range(7,38)]
    session_list=['0614','0616','0623','0624','0630','0701']
    for n in n_list:
        for w in w_list:
            for k in k_list:
                dataset_list=[]
                for i in range(len(session_list)):
                    dataset_list.append(scipy.io.loadmat('./{0}/{1}/{2}/'.format(n,w,k)+session_list[i]+'.mat'))
                CC,MSE=get_kalman_result(dataset_list)
                np.save('./{0}/{1}/{2}/'.format(n,w,k)+'CC.npy',CC)
                np.save('./{0}/{1}/{2}/'.format(n,w,k)+'MSE.npy',MSE)