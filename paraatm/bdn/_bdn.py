
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
    _get_rnn_model (internal method)
    _get_dnn_model (internal method)
    pred 
    """
    def __init__(self,x_train,y_train,idrop=0.25,
                 odrop=0.25,rdrop=0.25,
                 weight_decay=1e-4,lr=1e-3,num_unit=100,
                 batch_size=30,epochs=200,model_type = 'rnn', custom_model = None):
        
        """
        Parameters
        ----------
        x_train: array
            training data
        y_train: array
            training target
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
        model_type: str
            Specify the neural network type
            By default, it's set as 'rnn'
            model_type == 'rnn': generate results for the embedded rnn model
            model_type == 'dnn': generate results for the embedded dnn model
            model_type == 'custom': generate results for the customized model
            When model_type == 'custom', a customized model must be provided
        custom_model: None is set by default, otherwise is a  customized sequential model
        """
        self.x_train = x_train
        self.y_train = y_train
        self.idrop = idrop
        self.odrop = odrop
        self.rdrop = rdrop
        self.weight_decay = weight_decay
        self.lr = lr
        self.num_unit=num_unit
        self.batch_size = batch_size
        self.epochs = epochs
        self.model_type = model_type
        self.custom_model = custom_model
        
        if not isinstance(self.x_train,np.ndarray):
            raise Exception('Wrong type: expect an array!') 
         
        if self.model_type == 'rnn':
            self.model = self._get_rnn_model()  
            
        if self.model_type == 'dnn':
            self.model = self._get_dnn_model() 
       
        if self.model_type == 'custom':
            if self.custom_model is None:
                raise Exception('Expect a customized model!')
            else:
                self.model = self.custom_model
        ### fit the model with training data    
        self.model.fit(self.x_train,self.y_train,self.batch_size,
                      self.epochs,verbose = False)
            
    def _get_rnn_model(self):
        """
        Construct a recursive neural network (rnn) model which is then passed to 'pred'method if model_type =='rnn'.
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
        Construct a deep neural network (dnn) model which is then passed to 'pred' method if model_type =='dnn'.
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
        

    def pred(self, x_test, get_var = True,iter_=5):
        """
        pred is used to generate results for the deep learning model. To get uncertainty of the model, get_var should be set as 'True'. By doing this, multiple realizations are done for one test data. The output of the pred method is the raw prediction results. Below is a simple example of how to build a bayesian RNN model.
        
        from paraatm.bdn import Bdn
        import numpy as np
        rnn_model = Bdn(RNN_x_train,RNN_y_train)
        rnn_y_test_pred = rnn_model.pred(RNN_x_test, RNN_y_test)
        ### to obtain the mean and variance of the prediction:
        mean_pred = np.mean(rnn_y_test_pred,axis=0)
        var_pred = np.var(rnn_y_test_pred,axis=0)
        
        
        Parameters
        ----------
        x_test: array
            test data     
        get_var: Boolen
            Whether the prediction result is deterministic or with uncertainty
            By default: it's set as 'True'
            get_var == True: prediction with uncertainty
            get_var == False: deterministic result  
        iter_: int
            Number of realizations for each sample
            By default, it's set as 5
            This is only used when get_var == True
        
        Returns
        -------
        An array which is prediction for the test data
        The array has a shape as num_iter by num_test_data
        num_test_data: number of test data
        num_iter: number of iterations

        """
        model = self.model
        if get_var==True:
            f = K.function([model.layers[0].input,
                                K.learning_phase()],[model.layers[-1].output])
            results = []
            for i in range(iter_):
                results.append(np.squeeze(f([x_test,1])))
            results = np.array(results)
        if get_var == False:
            results = model.predict(x_test)
        return results
