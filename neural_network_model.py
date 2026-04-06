import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class LSTM_Net(nn.Module):
    
    def __init__(self,input_size,hidden_size,output_size):
        super(LSTM_Net,self).__init__()
        self.input_size=input_size
        self.output_size=output_size
        self.lstm=nn.LSTM(input_size,hidden_size,1,batch_first=True)
        self.fc1=nn.Linear(hidden_size, output_size)
        
    def forward(self,x):
        res=x.t()
        res,_=self.lstm(res.unsqueeze(0))
        res=self.fc1(F.elu(res))
        return res.squeeze(0).t()
    
class Classify_Net(nn.Module):
    
    def __init__(self,input_size,hidden_size,output_size):
        super(Classify_Net,self).__init__()
        self.input_size=input_size
        self.output_size=output_size
        self.lstm=nn.LSTM(input_size,hidden_size,1,batch_first=True)

        self.fc1=nn.Linear(hidden_size, output_size)
        
    def forward(self,x,hc=0,drop=1):
        res=x.t()
        res,_=self.lstm(res.unsqueeze(0))
        res=self.fc1(res[:,-1])
        return res

class trainer():
    
    def __init__(self,net,optimizer,loss_fn):
        self.net=net
        self.optimizer=optimizer
        self.loss_fn=loss_fn
        
    def train_one_epoch(self,data_list,vel_list,noise=0):
        train_loss=np.zeros(len(data_list))
        for i in range(len(data_list)):
            res=self.net(data_list[i],noise=noise)
            los=self.loss_fn(res,vel_list[i])
            self.optimizer.zero_grad()
            los.backward()
            self.optimizer.step()
            train_loss[i]=float(los)
        return train_loss
    
    def test(self,test,vel,return_res=0):
        res=self.net(test)
        los=self.loss_fn(res,vel)
        
        mse=float(los)
        if return_res==0:
            return mse,vel.shape[1]
        else:
            x_cc=float(torch.corrcoef(torch.stack([res[0],vel[0]],axis=0))[0,1])
            y_cc=float(torch.corrcoef(torch.stack([res[1],vel[1]],axis=0))[0,1])
            return x_cc,y_cc,mse,res.detach().cpu().numpy()
    
    def net_save(self,path):
        torch.save(self.net.state_dict(),path)
        return
        
    def net_load(self,path):
        self.net.load_state_dict(torch.load(path))
        return

class classify_trainer():
    
    def __init__(self,net,optimizer,loss_fn):
        self.net=net
        self.optimizer=optimizer
        self.loss_fn=loss_fn
        
    def train_one_turn(self,data_list,vel_list):
        train_loss=np.zeros(len(data_list))
        for i in range(len(data_list)):
            res=self.net(data_list[i],drop=0)
            los=self.loss_fn(res,vel_list[i])
            self.optimizer.zero_grad()
            los.backward()
            self.optimizer.step()
            train_loss[i]=float(los)
        return train_loss
    
    def test(self,test,vel,return_res=0):
        res=self.net(test,drop=0)
        los=self.loss_fn(res,vel)
        
        return float(los),(torch.argmax(res)==vel).cpu().numpy()
    
    def net_save(self,path):
        torch.save(self.net.state_dict(),path)
        return
        
    def net_load(self,path):
        self.net.load_state_dict(torch.load(path))
        return