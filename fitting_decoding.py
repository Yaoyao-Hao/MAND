'''
Related Figures:3a-c
'''
import os
import torch
import scipy.io
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from neural_network_model import*

def cut(feature_list,mask):
    '''
    Based on mask segmentation features (temporal sequence)
    '''
    if type(feature_list)==list and len(feature_list)!=mask.shape[0]:
        start_mark=0
        end_mark=start_mark
        n=len(mask)
        m=len(feature_list)
        res=[[] for i in range(m)]
        while True:
            start_mark=end_mark
            while True:
                end_mark=end_mark+1
                if end_mark==n or mask[start_mark]!=mask[end_mark]:
                    break
            for i in range(m):
                res[i].append(feature_list[i][:,start_mark:end_mark])
            if end_mark==n:
                break
    else:
        start_mark=0
        end_mark=start_mark
        res=[]
        while True:
            start_mark=end_mark
            while True:
                end_mark=end_mark+1
                if end_mark==len(mask) or mask[start_mark]!=mask[end_mark]:
                    break
            res.append(feature_list[:,start_mark:end_mark])
            if end_mark==len(mask):
                break
    return res

os.environ["CUDA_VISIBLE_DEVICES"] = "0,1,2,3"

if __name__ == "__main__":
    session_list=['./dataset/Human/ESA/']
    res_list=['0623']
    dataset_list=['0623.mat']
    single_start_path='./single_start_net.pth'
    single_best_path='./single_best_net.pth'
    for w in range(len(session_list)):
        net_model=LSTM_Net
        loss_fn=nn.MSELoss
        hidden_size=512
        optimizer=torch.optim.Adam
        optimizer_kw={'lr':0.001}
        best_end_interval=100
        
        for q,dataset in enumerate(dataset_list):
            a=scipy.io.loadmat(session_list[w]+dataset)
            a['bined_spk']=((a['bined_spk'].T-a['bined_spk'].mean(1))).T
            target_num=a['fold_num'].shape[1]
            trial_num=a['trial_target'].shape[0]
            net_args=[a['bined_spk'].shape[0],hidden_size,a['trial_velocity'].shape[0]]
            net_kw={}

            CC = np.zeros((trial_num,2))
            MSE = np.zeros((trial_num,1))
            prediction = [0 for i in range(trial_num)]
            
            ACCURACY = np.zeros((trial_num,1))
            prediction_classify=[0 for i in range(trial_num)]
            
            CC_dual = np.zeros((trial_num,2))
            MSE_dual = np.zeros((trial_num,1))
            prediction_dual = [0 for i in range(trial_num)]
            
            single_loss_fn=loss_fn().cuda()
            single_net=net_model(*net_args,**net_kw).cuda()
            single_optimizer=optimizer(single_net.parameters(),**optimizer_kw)
            single_trainer=trainer(single_net,single_optimizer,single_loss_fn)
            single_trainer.net_save(single_start_path)
            
            for i_target in range(a['fold_num'].shape[1]):
                target_ind = np.where(a['trial_target'] == i_target)[0]
                bins_remove = np.concatenate([np.where(a['trial_mask'] == target_ind[i])[1] for i in range(len(target_ind))],axis=0)
                trial_velocity_train=np.delete(a['trial_velocity'],bins_remove,axis=1)
                bined_spk_train=np.delete(a['bined_spk'],bins_remove,axis=1)
                trial_mask_train=np.delete(a['trial_mask'],bins_remove,axis=1)
                trial_velocity_train,bined_spk_train,break_ind_train=cut([trial_velocity_train,bined_spk_train,break_ind_train],trial_mask_train[0])
                for i in range(len(trial_velocity_train)):
                    trial_velocity_train[i]=torch.tensor(trial_velocity_train[i],dtype=torch.float32).cuda()
                    bined_spk_train[i]=torch.tensor(bined_spk_train[i],dtype=torch.float32).cuda()
                
                trial_velocity_test=a['trial_velocity'][:,bins_remove]
                bined_spk_test=a['bined_spk'][:,bins_remove]
                trial_mask_test=a['trial_mask'][:,bins_remove]
                trial_velocity_test,bined_spk_test,break_ind_test=cut([trial_velocity_test,bined_spk_test,break_ind_test],trial_mask_test[0])
                for i in range(len(trial_velocity_test)):
                    trial_velocity_test[i]=torch.tensor(trial_velocity_test[i],dtype=torch.float32).cuda()
                    bined_spk_test[i]=torch.tensor(bined_spk_test[i],dtype=torch.float32).cuda()
                
                single_trainer.net_load(single_start_path)
                mse_best=1e10
                iteration_best=0
                iteration=0
                
                while True:
                    mse=[]
                    length=[]
                    single_trainer.train_one_epoch(bined_spk_train, trial_velocity_train,noise=noise)
                    for i in range(len(trial_velocity_test)):
                        mse1,len1=single_trainer.test(bined_spk_test[i], trial_velocity_test[i])
                        mse.append(mse1)
                        length.append(len1)
                    mse_sum=0
                    len_sum=0
                    for i in range(len(mse)):
                        mse_sum=mse_sum+length[i]*mse[i]
                        len_sum=len_sum+length[i]
                    mse_sum=mse_sum/len_sum
                    if mse_sum<mse_best:
                        mse_best=mse_sum
                        iteration_best=iteration
                        single_trainer.net_save(single_best_path)
                    print('{0}-{1}-Loss:{2}'.format(i_target,iteration,mse_sum))
                    if iteration-iteration_best>best_end_interval:
                        break
                    iteration=iteration+1
                
                single_trainer.net_load(single_best_path)
                for i in range(len(target_ind)):
                    CC[target_ind[i],0],CC[target_ind[i],1],MSE[target_ind[i],0],prediction[target_ind[i]] = single_trainer.test(bined_spk_test[i], trial_velocity_test[i],return_res=1)
                
            create_path=dataset.split('/')[-1].split('.')[0]
            os.makedirs('/home/zju/xgx/result/{0}/{1}'.format(res_list[w],create_path))
            np.save('/home/zju/xgx/result/{0}/{1}/CC.npy'.format(res_list[w],create_path),CC)
            np.save('/home/zju/xgx/result/{0}/{1}/MSE.npy'.format(res_list[w],create_path),MSE)
            np.save('/home/zju/xgx/result/{0}/{1}/prediction.npy'.format(res_list[w],create_path),np.concatenate(prediction,axis=1))
        
