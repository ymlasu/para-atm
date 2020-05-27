import paraatm
from paraatm.bdn import BDN
import unittest
import numpy as np
import os

RNN_x_train = RNN_x_test = np.random.rand(10,2,2)
RNN_y_train = RNN_y_test = np.random.rand(10,)

DNN_x_train = DNN_x_test = np.random.rand(10,2)
DNN_y_train = DNN_y_test = np.random.rand(10,)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class TestBDN(unittest.TestCase):
    ### test the RNN network
    def test_DNN_input(self):
        DNN_x_train_path = os.path.join(THIS_DIR, '..', 'sample_data/BDN_data/bdn_DNN_x_train.npy')
        DNN_x_train = np.load(DNN_x_train_path)
        self.assertEqual(len(DNN_x_train.shape), 2)  
        
        DNN_x_test_path = os.path.join(THIS_DIR, '..', 'sample_data/BDN_data/bdn_DNN_x_test.npy')
        DNN_x_test = np.load(DNN_x_test_path)
        self.assertEqual(len(DNN_x_test.shape), 2)
        
        DNN_y_train_path = os.path.join(THIS_DIR, '..', 'sample_data/BDN_data/bdn_DNN_y_train.npy')
        DNN_y_train = np.load(DNN_y_train_path)
        self.assertEqual(len(DNN_y_train.shape), 1)  
        
        DNN_y_test_path = os.path.join(THIS_DIR, '..', 'sample_data/BDN_data/bdn_DNN_y_test.npy')
        DNN_y_test = np.load(DNN_y_test_path)
        self.assertEqual(len(DNN_y_test.shape), 1) 
        
    def test_RNN_input(self):
        RNN_x_train_path = os.path.join(THIS_DIR, '..', 'sample_data/BDN_data/bdn_RNN_x_train.npy')
        RNN_x_train = np.load(RNN_x_train_path)
        self.assertEqual(len(RNN_x_train.shape), 3)  
        
        RNN_x_test_path = os.path.join(THIS_DIR, '..', 'sample_data/BDN_data/bdn_RNN_x_test.npy')
        RNN_x_test = np.load(RNN_x_test_path)
        self.assertEqual(len(RNN_x_test.shape), 3)
        
        RNN_y_train_path = os.path.join(THIS_DIR, '..', 'sample_data/BDN_data/bdn_RNN_y_train.npy')
        RNN_y_train = np.load(RNN_y_train_path)
        self.assertEqual(len(RNN_y_train.shape), 1)  
        
        RNN_y_test_path = os.path.join(THIS_DIR, '..', 'sample_data/BDN_data/bdn_RNN_y_test.npy')
        RNN_y_test = np.load(RNN_y_test_path)
        self.assertEqual(len(RNN_y_test.shape), 1)         
                
    def test_RNN(self):
        rnn_model = BDN(RNN_x_train,RNN_y_train,RNN_x_test, RNN_y_test)
        rnn_y_test_pred = rnn_model.BDNpred(flag_1=False)
        self.assertEqual(rnn_y_test_pred.shape[1],1)
    ### test the DNN network
    def test_DNN(self):
        dnn_model = BDN(DNN_x_train,DNN_y_train,DNN_x_test, DNN_y_test)
        dnn_y_test_pred = dnn_model.BDNpred(flag_1 = False,flag_2 = 'DNN')
        self.assertEqual(dnn_y_test_pred.shape[1],1)
