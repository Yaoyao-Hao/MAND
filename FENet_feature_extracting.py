'''
Related Figures:s5
'''
import os
import torch
import scipy.io
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from sklearn.linear_model import LinearRegression

class WaveletConvolution(nn.Module):
    """
    A wrapper around two Conv1d layers, one (feat / hpf)which returns the
    intermediate value, and the other (feat / lpf) whose output is to be feated
    onto the next WaveletConvolution.

    `feat_out_channels` = number of convolutional channels the feature
                          convolution should output
    `features`          = number of wavelet transform features this layer
                          should produce, from AdaptiveAvgPool-ing the output
                          of the feat_l conv layer
    """
    def __init__(self, in_channels, features,
                       feat_out_channels, feat_kernel_size, feat_stride,
                       pass_out_channels, pass_kernel_size, pass_stride,
                       feat_kwargs={}, pass_kwargs={},
                       dropout=0.2, activation_fn=nn.LeakyReLU(-1),
                       cache_intermediate_outputs=False,
                       num_to_cache=None):
        """
        Use the `feat_kwargs` and `pass_kwargs` arguments to forward optional
        arguments to the underlying nn.Conv1d layers.

        Expects an element-wise `activation_fn`, eg. not softmax.
        Uses LeakyReLU with negative slope -1 to simulate absolute value by
        default, to make this more analogous to wavelet transform.
        """
        super(WaveletConvolution, self).__init__()
        from math import ceil


        self.feat_l = nn.Conv1d(in_channels, feat_out_channels, feat_kernel_size, feat_stride, **feat_kwargs)
        self.pass_l = nn.Conv1d(in_channels, pass_out_channels, pass_kernel_size, pass_stride, **pass_kwargs)
        self.feat_pad = nn.ConstantPad1d((ceil(max((feat_kernel_size - feat_stride), 0)), feat_kernel_size - 1), 0)
        self.pass_pad = nn.ConstantPad1d((ceil(max((pass_kernel_size - pass_stride), 0)), pass_kernel_size - 1), 0)

        if feat_out_channels > 1:
            raise NotImplementedError("FENet reimplementation cannot currently handle more than one conv out filter, since that would mix neural channels and convolutional channels/filters. see tag todo-multiconvchannel")
        else:
            self.features = features
            self.pool = nn.AdaptiveAvgPool1d(features)  # todo-multiconvchannel: to enable feat_out_channels > 1, use AdaptiveAvgPool2d
            #self.pool = BitshiftApproxAveragePool()    # divide by nearest power of 2 instead, bc hardware
        self.dropout = dropout
        self.activation_fn = activation_fn
        self._cache = cache_intermediate_outputs
        self.num_to_cache = num_to_cache
        self.output_cache = [None]*2

    def forward(self, x):
        """
        Expects shape = (batch_size * neural_channels, in_channels, n_samples)
        Returns shape = (batch_size, 1, features*feat_out_channels), (batch_size, pass_out_channels, convolved_len)
        """
        batch_size, n_channels, n_samples = x.shape

        feat_x = self.feat_pad(x)
        pass_x = self.pass_pad(x)

        feat_x = self.feat_l(feat_x)
        pass_x = self.pass_l(pass_x)
        feat_x = self.activation_fn(feat_x)

        num_to_cache = batch_size if self.num_to_cache is None else self.num_to_cache

        if self._cache: self.output_cache[0] = self.activation_fn(pass_x[0:num_to_cache, :, :])
        if self._cache: self.output_cache[1] = feat_x[0:num_to_cache, :, :]

        feat_x = self.pool(feat_x)
        feat_x = feat_x.view(batch_size, self.features) # flatten feat_x into 1d array per batch-element*neural-channel

        pass_x = F.dropout(pass_x, p=self.dropout, training=self.training)

        return feat_x, pass_x

# TODO: quantize before pooling

class FENet(nn.Module):
    def __init__(self,
                 features_by_layer=[1]*8,
                  kernel_by_layer=[40]*7,
                   stride_by_layer=[2]*7,
                   relu_by_layer=[0]*7,
                    checkpoint_name=None,
                           pls_dims=None,
                             dropout=0.2,
                  normalize_at_end=False,

                     cache_intermediate_outputs=False,
                     num_to_cache=None,

                    annealing_alpha=0.01,
                     thermal_sigma=0.001,
                    anneal_eval_window=8,
                            anneal=False,
                     ):
        """
        `features_by_layer`: an array of how many features each layer should return. The last element is the number of features of the output of the full convolutional stack.
        """
        super(FENet, self).__init__()

        if len(features_by_layer)-1 != len(kernel_by_layer) or len(features_by_layer)-1 != len(stride_by_layer) or len(features_by_layer)-1 != len(relu_by_layer):
            print(features_by_layer, kernel_by_layer, stride_by_layer, relu_by_layer)
            raise ValueError("`features_by_layer`[:-1], `sizes_by_layer`, and `strides_by_layer`, and 'relu_by_layer' must be same len")

        # todo-experiment: allow different kernel sizes and strides for feat_l and pass_l

        jank_serialize = lambda int_list: '-'.join(str(x) for x in int_list)
        self.checkpoint_name = checkpoint_name or f"training_{jank_serialize(features_by_layer)}_{jank_serialize(kernel_by_layer)}_{jank_serialize(stride_by_layer)}" # used to identify models when logging
        self.pls = pls_dims  # TODO: Create a FENet Pipeline class that handles different PLS and Decoder things

        self.features_by_layer = features_by_layer
        self.kernel_by_layer = kernel_by_layer
        self.stride_by_layer = stride_by_layer
        self.relu_by_layer = relu_by_layer
        self.activation_fn = [nn.LeakyReLU(-1/(2**int(power))) for power in relu_by_layer]  ## TODO: shouldbe corrected
        self.poolDivisor = [0]*len(kernel_by_layer)
        self.layers = nn.ModuleList([
            WaveletConvolution(
                in_channels=1, features=feats,
                feat_out_channels=1, feat_kernel_size=kernel, feat_stride=stride, feat_kwargs={ 'bias': False },
                pass_out_channels=1, pass_kernel_size=kernel, pass_stride=stride, pass_kwargs={ 'bias': False },
                dropout=dropout, activation_fn=activation_fn,
                cache_intermediate_outputs=cache_intermediate_outputs, num_to_cache=num_to_cache
            )
            for feats, kernel, stride, activation_fn in zip(features_by_layer[:-1], kernel_by_layer, stride_by_layer, self.activation_fn) ])

        # self.anneal_noise = [[(torch.randn(weights_pass.size(), device=weights_pass.device) * annealing_alpha,
        #                        torch.randn(weights_feat.size(), device=weights_feat.device) * annealing_alpha)
        #     for weights_pass, weights_feat in zip(layer.pass_l.parameters(), layer.feat_l.parameters())]
        #     for layer in self.layers]
        # self.pool = BitshiftApproxAveragePool()
        self.pool = nn.AdaptiveAvgPool1d(1)
        # self.bn = nn.BatchNorm1d(sum(self.features_by_layer), affine = False, track_running_stats = False) if normalize_at_end else None
        self.normalize_at_end = normalize_at_end  # FIXME: actually take in n_channels and construct the batchnorm


        self.annealing_alpha = annealing_alpha
        self.thermal_sigma = thermal_sigma
        self.running_annealed_loss = 0
        self.running_non_annealed_loss = 0
        self.loss_recieved_counter = 0
        self.anneal_eval_window = anneal_eval_window
        self.anneal=anneal

    def forward(self, x, use_annealed_weights=False):
        """
        Expects a tensor of electrode streams, shape = (batch_size, n_channels=192, n_samples=900)
        Returns a tensor of electrode features, shape = (batch_size, n_channels=192, sum(features_by_layer))
        """
        n_chunks, n_channels, n_samples = x.shape
        x = x.reshape(n_chunks * n_channels, 1, n_samples)  # FIXME: why do we get an error when using view? where's the non-contiguous data coming from?
        features_list = []  # todo-optm: preallocate zeros, then copy feat_x output into the ndarray
        pass_x = x

        # feed `x` through FENet, storing intermediate `feat_x`s along the way
        # if(self.anneal and use_annealed_weights):
            # annealed_layers = self.layers
            # for anneal_noise, wvlt_cnn_layer in zip(self.anneal_noise, annealed_layers):
                # for pass_noise, feat_noise, weights_pass, weights_feat in zip(anneal_noise[0][0],
                                                                            #   anneal_noise[0][1],
                                                        #    wvlt_cnn_layer.pass_l.parameters(),
                                                        #    wvlt_cnn_layer.feat_l.parameters()):
                    # weights_pass.add_(pass_noise.to(weights_pass.device))
                    # weights_feat.add_(feat_noise.to(weights_feat.device))

        # for wvlt_cnn_layer in tqdm(annealed_layers if (use_annealed_weights and self.anneal) else self.layers, desc="fenet layer", leave=False):
        # for wvlt_cnn_layer in (annealed_layers if (use_annealed_weights and self.anneal) else self.layers):
        for wvlt_cnn_layer in self.layers:
            feat_x, pass_x = wvlt_cnn_layer(pass_x)
            features_list.append(feat_x)
            del(feat_x)
            torch.cuda.empty_cache()


        # end case: non-linear + adaptive_avgpool the output of the
        # WaveletConvolution stack to create the final feature
        final_feat = self.activation_fn[-1](pass_x)
        final_feat = self.pool(final_feat)
        final_feat = final_feat.view(-1, self.features_by_layer[-1]) # flatten feat_x into 1d array per batch-element*neural-channel
        features_list.append(final_feat)

        # concatenate the features from each layer for the final output
        x_total_feat = torch.cat(features_list, dim=1)
        x_total_feat = x_total_feat.view(-1, n_channels * sum(self.features_by_layer))
        if self.normalize_at_end:
            bn = nn.BatchNorm1d(sum(self.features_by_layer) * n_channels, affine=False, track_running_stats=False) # FIXME: slow
            x_total_feat = bn(x_total_feat)

        return x_total_feat

class feature_extract_net(nn.Module):
    def __init__(self):
        super(feature_extract_net,self).__init__()
        self.fenet=FENet()
        self.dropout=nn.Dropout(0.2)
        self.Linear1=nn.Linear(8, 1)
        self.Linear2=nn.Linear(96, 2)
        self.Linear2.weight.requires_grad = False
        self.Linear2.bias.requires_grad = False

    def forward(self,x,return_feature=False):
        nc,nt,_=x.shape
        feature=self.fenet(x.transpose(0, 1))
        feature=self.dropout(feature)
        feature=self.Linear1(feature.view(nt,-1,8)).squeeze()

        res=self.Linear2(feature.unsqueeze(0))
        if return_feature:
            return res.squeeze(0).transpose(0, 1),feature.transpose(0, 1)
        else:
            return res.squeeze(0).transpose(0, 1)
    
    def update(self,w,b):
        self.Linear2.weight.copy_(torch.tensor(w,dtype=self.Linear2.weight.dtype,device=self.Linear2.weight.device))
        self.Linear2.bias.copy_(torch.tensor(b,dtype=self.Linear2.bias.dtype,device=self.Linear2.bias.device))

class feature_extract_trainer():
    
    def __init__(self,net,optimizer,loss_fn):
        self.net=net
        self.optimizer=optimizer
        self.loss_fn=loss_fn
        
    def train(self,data_path,trial_list,vel_list,epoch):
        if epoch % 10 == 0:
            for p in self.optimizer.param_groups:
                p['lr'] *= 0.5
        self.net.train()
        for i in range(len(trial_list)):
            data=np.load(data_path+'{0}.npy'.format(trial_list[i]))
            data=torch.tensor(data,dtype=torch.float32).cuda()
            res=self.net(data)
            los=self.loss_fn(res,vel_list[i])
            self.optimizer.zero_grad()
            los.backward()
            self.optimizer.step()
        self.net.eval()
        res_list=[]
        v_list=[]
        for i in range(len(trial_list)):
            data=np.load(data_path+'{0}.npy'.format(trial_list[i]))
            data=torch.tensor(data,dtype=torch.float32).cuda()
            _,res=self.net(data,return_feature=True)
            res_list.append(res.detach().cpu().numpy())
            v_list.append(vel_list[i].cpu().numpy())
        res_list=np.concatenate(res_list, axis=1).T
        v_list=np.concatenate(v_list, axis=1).T
        model = LinearRegression()
        model.fit(res_list, v_list)
        self.net.update(model.coef_,model.intercept_)
    
    def test(self,test,vel,return_feature=0):
        self.net.eval()
        res,feature=self.net(test,return_feature=True)
        los=self.loss_fn(res,vel)
        mse=float(los)
        if return_feature==0:
            return mse,vel.shape[1]
        else:
            return feature.detach().cpu().numpy()
    
    def net_save(self,path):
        torch.save(self.net.state_dict(),path)
        return
        
    def net_load(self,path):
        self.net.load_state_dict(torch.load(path))
        return
    
def cut(feature_list,mark_list,lists=0):
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

os.environ["CUDA_VISIBLE_DEVICES"] = "3,0,1,2"

if __name__ == "__main__":
    day_list=['0614','0616','0623','0624','0630','0701']
    path_list=['/home/zju/xgx/dataset/handwriting/ESA/']
    res_list=['FENet_hand']
    dataset_list=['/home/zju/xgx/dataset/handwriting/raw/trial/'+i+'/' for i in day_list]#raw data segment
    label_list=[i+'.mat' for i in day_list]
    single_start_path='./single_start_net.pth'
    single_best_path='./single_best_net.pth'
    for w in range(len(path_list)):
        net_model=feature_extract_net
        loss_fn=nn.MSELoss
        hidden_size=512
        optimizer=torch.optim.Adam
        optimizer_kw={'lr':0.2,'weight_decay':1e-4}
        best_end_interval=20
        
        for q,dataset in enumerate(label_list):
            data_path=dataset_list[q]
            a=scipy.io.loadmat(path_list[w]+dataset)
            a['bined_spk']=((a['bined_spk'].T-a['bined_spk'].mean(1))).T
            target_num=a['fold_num'].shape[1]
            trial_num=a['trial_target'].shape[0]
            net_args=[a['bined_spk'].shape[0],hidden_size,a['trial_velocity'].shape[0],False]
            net_kw={}
            
            CC = np.zeros((trial_num,2))
            MSE = np.zeros((trial_num,1))
            feature = [0 for i in range(trial_num)]
            prediction = [0 for i in range(trial_num)]
            
            single_loss_fn=loss_fn().cuda()
            single_net=net_model().cuda()
            single_optimizer=optimizer(single_net.parameters(),**optimizer_kw)
            single_trainer=feature_extract_trainer(single_net,single_optimizer,single_loss_fn)
            single_trainer.net_save(single_start_path)
            
            target_ind=np.concatenate([np.where(a['trial_target']-1 == i)[0][int(np.where(a['trial_target']-1 == i)[0].shape[0]/3*2):] for i in range(a['fold_num'].shape[1])],axis=0)
            bins_remove = np.concatenate([np.where(a['trial_mask']-1 == target_ind[i])[1] for i in range(len(target_ind))],axis=0)
            trial_velocity_train=np.delete(a['trial_velocity'],bins_remove,axis=1)
            bined_spk_train=np.delete(np.arange(a['trial_target'].shape[0]),target_ind)
            trial_mask_train=np.delete(a['trial_mask'],bins_remove,axis=1)
            trial_velocity_train=cut(trial_velocity_train,trial_mask_train[0],lists=0)
            for i in range(len(trial_velocity_train)):
                trial_velocity_train[i]=torch.tensor(trial_velocity_train[i],dtype=torch.float32).cuda()
            
            
            trial_velocity_test=a['trial_velocity'][:,bins_remove]
            bined_spk_test=np.arange(a['trial_target'].shape[0])[target_ind]
            trial_mask_test=a['trial_mask'][:,bins_remove]
            trial_velocity_test=cut(trial_velocity_test,trial_mask_test[0],lists=0)
            for i in range(len(trial_velocity_test)):
                trial_velocity_test[i]=torch.tensor(trial_velocity_test[i],dtype=torch.float32).cuda()
            
            single_trainer.net_load(single_start_path)
            mse_best=1e10
            iteration_best=0
            iteration=0
            
            while True:
                mse=[]
                length=[]
                single_trainer.train(data_path,bined_spk_train,trial_velocity_train,iteration)
                for i in range(len(trial_velocity_test)):
                    data=np.load(data_path+'{0}.npy'.format(bined_spk_test[i]))
                    data=torch.tensor(data,dtype=torch.float32).cuda()
                    mse1,len1=single_trainer.test(data, trial_velocity_test[i])
                    mse.append(mse1)
                    length.append(len1)
                mse_sum=0
                len_sum=0
                for i in range(len(mse)):
                    mse_sum=mse_sum+length[i]*mse[i]
                    len_sum=len_sum+length[i]
                mse_sum=mse_sum/len_sum
                if mse_sum<mse_best*0.999:
                    mse_best=mse_sum
                    iteration_best=iteration
                    single_trainer.net_save(single_best_path)
                print('{0}-single MSE:{1}'.format(iteration,mse_sum))
                if iteration-iteration_best>best_end_interval:
                    break
                iteration=iteration+1
            
            single_trainer.net_load(single_best_path)
            bined_spk=np.concatenate([bined_spk_train,bined_spk_test],axis=0)
            trial_velocity=trial_velocity_train+trial_velocity_test
            for i in range(bined_spk.shape[0]):
                data=np.load(data_path+'{0}.npy'.format(bined_spk[i]))
                data=torch.tensor(data,dtype=torch.float32).cuda()
                feature[bined_spk[i]] = single_trainer.test(data, trial_velocity[i],return_feature=1)
            
            create_path=dataset.split('/')[-1].split('.')[0]
            os.makedirs('/home/zju/xgx/result/{0}/{1}'.format(res_list[w],create_path))
            np.save('/home/zju/xgx/result/{0}/{1}/feature.npy'.format(res_list[w],create_path),np.concatenate(feature,axis=1))
