"""
Bayesian deep neural network (BDN) class
---
Required pakages:
keras
numpy

"""
import keras.backend as K
from keras.models import Model
from keras.layers import Input, Dense, Dropout,LSTM,Activation
from keras.optimizers import Adam
from keras.regularizers import l1,l2
from keras.models import Sequential
import numpy as np

class BDN(object):
    """
    BDN class creates bayesian deep neural network and provides 
    predictions with uncertainty
    
    Reference: Gal, Y., & Ghahramani, Z. (2016, June). Dropout as a bayesian approximation: Representing model uncertainty in deep learning. In international conference on machine learning (pp. 1050-1059).
    
    Attributes
    ----------
    x_train: training data
    y_train: training target
    x_test: test data
    y_test: test target
    idrop: dropout rate for input layer
    odrop: dropout rate for output layer
    rdrop:dropout rate for the recurrent layer(DNN model doesn't need rdrop
    but is provided by default)
    weight_decay: regularization factor
    lr: learning rate
    num_unit: number of unit at each layer
    batch_size: mini batch size
    epochs: number of epochs
    iter_: number of predictions for each sample
    results: array of predicted results for the test data.
    
    Methods:
    -------
    get_RNN_model
    get_DNN_model
    BDNpred
    
    """
    def __init__(self,x_train,y_train,x_test,y_test,idrop=0.,
                 odrop=0.25,rdrop=0.25,
                 weight_decay=1e-4,lr=1e-3,num_unit=100,
                 batch_size=30,epochs=200,iter_=5):
        self.x_train = x_train
        self.y_train = y_train
        self.x_test = x_test
        self.y_test = y_test
        self.idrop = idrop
        self.odrop = odrop
        self.rdrop = rdrop
        self.weight_decay = weight_decay
        self.lr = lr
        self.num_unit=num_unit
        self.batch_size = batch_size
        self.epochs = epochs
        self.iter_ = iter_
        if not isinstance(self.x_train,np.ndarray):
            raise Exception('Wrong type: expect an array!') 

    def get_RNN_model(self):
        if len(self.x_train.shape)!=3:
            raise Exception('expect a 3 dimension array!')
        in_shape = self.x_train.shape[-1]
        model=Sequential()
        model.add(LSTM(self.num_unit,kernel_regularizer=l2(self.weight_decay),
                       recurrent_regularizer=l2(self.weight_decay),
                       bias_regularizer=l2(self.weight_decay),dropout=self.idrop,
                       recurrent_dropout=self.rdrop,input_shape=(None, in_shape),
                      kernel_initializer='random_uniform',return_sequences=True))

        model.add(Activation('relu'))

        model.add(LSTM(self.num_unit,dropout=self.idrop,
                       recurrent_dropout=self.rdrop,return_sequences=False,
                       kernel_regularizer=l2(self.weight_decay),
                       recurrent_regularizer=l2(self.weight_decay),
                       bias_regularizer=l2(self.weight_decay)))
        model.add(Activation('relu'))
        if self.odrop:
            model.add(Dropout(self.odrop))
        model.add(Dense(1,activation='linear',
                        kernel_regularizer=l2(self.weight_decay),
                        bias_regularizer=l2(self.weight_decay)))
        optimizer_=Adam(self.lr)
        model.compile(loss='mse',metrics=['mse'],optimizer=optimizer_)
        return model
    def get_DNN_model(self):

        if len(self.x_train.shape)!=2:
            raise Exception('expect a 2 dimension array!')
        in_shape = self.x_train.shape[-1]
        model=Sequential()
        model.add(Dense(self.num_unit,kernel_regularizer=l2(self.weight_decay),
                       bias_regularizer=l2(self.weight_decay),
                        kernel_initializer='random_uniform',
                        input_dim=in_shape))
        
        model.add(Activation('relu'))
        model.add(Dropout(self.idrop))
        model.add(Dense(self.num_unit,kernel_regularizer=l2(self.weight_decay),
                       bias_regularizer=l2(self.weight_decay),
                        kernel_initializer='random_uniform',
                       ))
        model.add(Dropout(self.idrop))
        model.add(Activation('relu'))  
        if self.odrop:
            model.add(Dropout(self.odrop))
        model.add(Dense(1,activation='linear',
                        kernel_regularizer=l2(self.weight_decay),
                        bias_regularizer=l2(self.weight_decay)))
        optimizer_=Adam(self.lr)
        model.compile(loss='mse',metrics=['mse'],optimizer=optimizer_)
        return model        
        

    def BDNpred(self,flag_1 = True,flag_2 = 'RNN',custom_model = None):
        """
        BDNpred is used to generate results for the deep learning model
        
        Attributes
        ----------
        flag_1==True: prediction with uncertainty
        flag_1==False: deterministic result
        
        flag_2 == 'RNN': generate results for the embedded RNN model
        flag_2 == 'DNN': generate results for the embedded DNN model
        flag_2 == 'custom': generate results for the customized model
        
        """
        if flag_2 =='RNN':
            model = self.get_RNN_model()
        if flag_2 =='DNN':
            model = self.get_DNN_model()
        if flag_2 =='custom':
            model = custom_model
        #print(model.summary())
        model.fit(self.x_train,self.y_train,self.batch_size,
                      self.epochs,verbose = False)
        if flag_1==True:
            f = K.function([model.layers[0].input,
                                K.learning_phase()],[model.layers[-1].output])
            results = []
            for i in range(self.iter_):
                results.append(np.squeeze(f([self.x_test,1])))
            results = np.array(results)
        if flag_1 == False:
            results = model.predict(self.x_test)
        return results
