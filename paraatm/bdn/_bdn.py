"""
Bayesian deep neural network (BDN) class
---
Required packages:
keras
tensorflow (as a banckend of keras)
numpy

"""
import warnings
# Ignore warnings during import with keras 2.3.1 and numpy 1.18.1
warnings.simplefilter(action="ignore", category=FutureWarning)

import keras.backend as K
from keras.models import Model
from keras.layers import Input, Dense, Dropout,LSTM,Activation
from keras.optimizers import Adam
from keras.regularizers import l1,l2
from keras.models import Sequential
import numpy as np

class Bdn(object):
    """
    Bdn class creates bayesian deep neural network and provides 
    predictions with uncertainty
    
    Reference: Gal, Y., & Ghahramani, Z. (2016, June). Dropout as a bayesian approximation: Representing model uncertainty in deep learning. In international conference on machine learning (pp. 1050-1059).
    
    Methods:
    -------
    get_rnn_model (internal method)
    get_dnn_model (internal method)
    pred 
    """
    def __init__(self,x_train,y_train,x_test,y_test,idrop=0.,
                 odrop=0.25,rdrop=0.25,
                 weight_decay=1e-4,lr=1e-3,num_unit=100,
                 batch_size=30,epochs=200,iter_=5):
        """
        Parameters
        ----------
        x_train: array
            training data
        y_train: array
            training target
        x_test: array
            test data
        y_test: array
            test target
        idrop: float
            dropout rate for input layer
        odrop: float
            dropout rate for output layer
        rdrop: float
            dropout rate for the recurrent layer (dnn model doesn't need rdrop
        but is provided by default)
        weight_decay: float
            regularization factor
        lr: float
            learning rate
        num_unit: int
            number of unit at each layer
        batch_size: int
            mini batch size
        epochs: int
            number of epochs
        iter_: int
            number of predictions for each sample
        """
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

    def _get_rnn_model(self):
        """
        Construct a recursive neural network (rnn) model which is then passed to 'pred'method if flag_2 =='rnn'.
        A rnn model is used to make predictions for temporal sequential data.
        
        For more information about rnn model, please refer to:
        https://en.wikipedia.org/wiki/Recurrent_neural_network
        
        Returns
        -------
        A sequential rnn model ready to be fit in 
        """
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
    def _get_dnn_model(self):
        """
        Construct a deep neural network (dnn) model which is then passed to 'pred' method if flag_2 =='dnn'.
        A dnn model is used to make predictions for input data which has linear or non-linear relationships with the output data, or target.
        
        
        For more information about dnn model, please refer to:
        https://en.wikipedia.org/wiki/Deep_learning#Deep_neural_networks
        
        Returns
        -------
        A sequential dnn model ready to be fit in 
        """
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
        

    def pred(self,flag_1 = True,flag_2 = 'rnn',custom_model = None):
        """
        pred is used to generate results for the deep learning model
        
        Parameters
        ----------
        flag_1: Boolen
            By default: it's set as 'True'
            flag_1 == True: prediction with uncertainty
            flag_1 == False: deterministic result
        
        flag_2: str
            By default, it's set as 'rnn'
            flag_2 == 'rnn': generate results for the embedded rnn model
            flag_2 == 'dnn': generate results for the embedded dnn model
            flag_2 == 'custom': generate results for the customized model
            When flag_2 == 'custom', a customized model must be provided
        
        custom_model: None is set by default, otherwise is a  customized sequential model
        
        Returns
        -------
        An array which is predictions for the test data
        The array has a shape as num_test_data by num_iter
        num_test_data:  Number of test data
        num_iter: number of iterations
        """
        if flag_2 =='rnn':
            model = self._get_rnn_model()
        if flag_2 =='dnn':
            model = self._get_dnn_model()
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
