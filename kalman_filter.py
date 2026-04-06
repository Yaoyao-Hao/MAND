'''
Related Figures:3b-c
'''
import numpy as np

class kalman_filter():
    def __init__(self,trainX,trainY):
        X1=trainY[:,0:-1]
        X2=trainY[:,1:]
        A=np.dot(((X2)@(X1.T)),np.mat(X1@(X1.T)).I.A)
        H=np.dot((trainX@(trainY.T)),np.mat(trainY@(trainY.T)).I.A)
        n=trainY.shape[1]
        W=((X2-A@X1)@((X2-A@X1).T))/(n-1)
        Q=((trainX-H@trainY)@((trainX-H@trainY).T))/n
        self.A=A
        self.H=H
        self.W=W + 1e-6 * np.eye(2)
        self.Q=Q + 1e-6 * np.eye(96)
    
    def fit(self,testX,testY):
        m=testY.shape[0]
        n=testX.shape[1]
        prediction=np.zeros((m,n))
        prediction[:,0]=np.ones_like(testY[:,0])
        P=np.eye(m)
        
        for i in range(1,n):
            Xn=self.A@prediction[:,i-1]
            P_=self.A@P@(self.A.T)+self.W
            
            K=P@(self.H.T)@np.linalg.pinv(self.H@P_@(self.H.T)+self.Q)
            prediction[:,i]=Xn+K@(testX[:,i]-self.H@Xn)
            P=(np.eye(m)-K@self.H)@P_

        x_cc=np.corrcoef(testY[0,:],prediction[0,:])
        y_cc=np.corrcoef(testY[1,:],prediction[1,:])
        CC = [x_cc[0,1],y_cc[0,1]];
        MSE = np.square(testY-prediction).mean()
        return CC,MSE,prediction

        