'''
Related Figures:3d
'''
import os
import torch
import scipy.io
import torch.nn as nn
import numpy as np
from neural_network_model import*

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


if __name__ == "__main__":
    hz_list=['H:/grasp/MUA/']
    res_list=['MUA']
    dataset_list=['101210.mat','140703.mat']
    single_start_path='./single_start_net.pth'
    single_best_path='./single_best_net.pth'
    classify_start_path='./classify_start_net.pth'
    classify_best_path='./classify_best_net.pth'
    for w in range(len(hz_list)):
        net_model=Classify_Net
        loss_fn=nn.CrossEntropyLoss
        hidden_size=512
        output_size=4
        optimizer=torch.optim.Adam
        optimizer_kw={'lr':0.001}
        best_end_interval=10
        
        for q,dataset in enumerate(dataset_list):
            a=scipy.io.loadmat(hz_list[w]+dataset)
            a['bined_spk']=((a['bined_spk'].T-a['bined_spk'].mean(1))).T
            if q==0:
                a['bined_spk'][[1,3,28]]=0
            target_num=a['fold_num'].shape[1]
            trial_num=a['trial_target'].shape[0]
            net_args=[a['bined_spk'].shape[0],hidden_size,output_size]
            net_kw={}
            
            loss = np.zeros((trial_num,1))
            prediction = np.zeros(trial_num)
            
            single_loss_fn=loss_fn().cuda()
            single_net=net_model(*net_args,**net_kw).cuda()
            single_optimizer=optimizer(single_net.parameters(),**optimizer_kw)
            single_trainer=classify_trainer(single_net,single_optimizer,single_loss_fn)
            single_trainer.net_save(classify_start_path)
            
            for i_target in range(a['fold_num'].shape[1]):
                target_ind = np.where(a['trial_target']-1 == i_target)[0]
                bins_remove = np.concatenate([np.where(a['trial_mask']-1 == target_ind[i])[1] for i in range(len(target_ind))],axis=0)
                bined_spk_train=np.delete(a['bined_spk'],bins_remove,axis=1)
                trial_mask_train=np.delete(a['trial_mask'],bins_remove,axis=1)
                bined_spk_train=cut(bined_spk_train,trial_mask_train[0],lists=0)
                label_train=np.delete(a['label'].T,target_ind,axis=0)
                for i in range(len(bined_spk_train)):
                    bined_spk_train[i]=torch.tensor(bined_spk_train[i],dtype=torch.float32).cuda()
                label_train=torch.tensor(label_train,dtype=torch.int64).cuda()
                    
                bined_spk_test=a['bined_spk'][:,bins_remove]
                trial_mask_test=a['trial_mask'][:,bins_remove]
                bined_spk_test=cut(bined_spk_test,trial_mask_test[0],lists=0)
                label_test=a['label'].T[target_ind]
                for i in range(len(bined_spk_test)):
                    bined_spk_test[i]=torch.tensor(bined_spk_test[i],dtype=torch.float32).cuda()
                label_test=torch.tensor(label_test,dtype=torch.int64).cuda()
                
                single_trainer.net_load(classify_start_path)
                loss_min=1e10
                iteration_best=0
                iteration=0
                
                while True:
                    loss=[]
                    single_trainer.train_one_turn(bined_spk_train, label_train)
                    for i in range(len(bined_spk_test)):
                        los,right=single_trainer.test(bined_spk_test[i], label_test[i])
                        loss.append(los)
                    loss_mean=np.array(loss).mean()
                    if loss_mean<loss_min:
                        loss_min=loss_mean
                        iteration_best=iteration
                        single_trainer.net_save(classify_best_path)
                    print('{0}-{1}-Loss:{2}'.format(i_target,iteration,loss_mean))
                    if iteration-iteration_best>best_end_interval:
                        break
                    iteration=iteration+1
                
                single_trainer.net_load(classify_best_path)
                for i in range(len(target_ind)):
                    loss[target_ind[i],0],prediction[target_ind[i]] = single_trainer.test(bined_spk_test[i], label_test[i],return_res=1)
                
                
            create_path=dataset.split('/')[-1].split('.')[0]
            os.makedirs('./{0}/{1}'.format(res_list[w],create_path))
            np.save('./{0}/{1}/loss.npy'.format(res_list[w],create_path),loss)
            np.save('./{0}/{1}/prediction.npy'.format(res_list[w],create_path),prediction)
