'''
Related Figures:3d
'''
import numpy as np
import scipy.io
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

def rescale_array(arr, new_size):
    old_size = arr.shape[0]
    scale_factor = new_size / old_size
    new_arr = np.interp(np.arange(0, new_size), np.arange(0, old_size) * scale_factor, arr)
    return new_arr

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

if __name__=="__main__":
    data=scipy.io.loadmat('H:/grasp/MAD_11/140703.mat')
    bined_spk=cut(data['bined_spk'],data['trial_mask'][0],lists=0)
    
    ww=data['trial_target']
    
    num=data['label'].shape[1]
    
    n_clusters=4
    label=data['label'][0]
    
    feature=[]
    for i in bined_spk:
        t=np.zeros((96,30))
        for j in range(96):
            t[j]=rescale_array(i[j],30)
        feature.append(t)
    feature=np.stack(feature).reshape(num,-1)
    
    X_train, X_test, y_train, y_test = train_test_split(feature, label, test_size=0.2, random_state=42)
    for i in range(5):
        X_train=np.delete(feature,np.where(ww==(i+1))[0],axis=0)
        y_train=np.delete(label,np.where(ww==(i+1))[0],axis=0)
        X_test=feature[np.where(ww==(i+1))[0]]
        y_test=label[np.where(ww==(i+1))[0]]

        sc = StandardScaler()
        sc.fit(X_train)
        X_train_std = sc.transform(X_train)
        X_test_std = sc.transform(X_test)

        svm = SVC(kernel='linear', C=1.0, random_state=1)
        svm.fit(X_train_std, y_train)

        y_pred = svm.predict(X_test_std)
        
        accuracy = accuracy_score(y_test, y_pred)
        print(accuracy,end=',')