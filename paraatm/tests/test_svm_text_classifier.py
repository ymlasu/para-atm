import paraatm
from paraatm.svm import SVM_text_class
import unittest
import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

class TestSVM(unittest.TestCase):
    
    def test_SVM_input(self):
        x_train_path = os.path.join(THIS_DIR, '..', 'sample_data/SVM_text_classifier/x_train.csv')
        df1 = pd.read_csv(x_train_path)
        # Simple check:
        self.assertEqual(len(df1), 500)
        
        y_train_path = os.path.join(THIS_DIR, '..', 'sample_data/SVM_text_classifier/y_train.csv')
        df2 = pd.read_csv(y_train_path)
        # Simple check:
        self.assertEqual(len(df2), 500)
        
        test_data_path = os.path.join(THIS_DIR, '..', 'sample_data/SVM_text_classifier/test_data.csv')
        df3 = pd.read_csv(test_data_path)
        # Simple check:
        self.assertEqual(len(df3), 150)
        
                     
    def test_SVM_classifier(self):
        x_train_path = os.path.join(THIS_DIR, '..', 'sample_data/SVM_text_classifier/x_train.csv')
        df1 = pd.read_csv(x_train_path)
        X_train = df1['Synopsis']

        y_train_path = os.path.join(THIS_DIR, '..', 'sample_data/SVM_text_classifier/y_train.csv')
        df2 = pd.read_csv(y_train_path)
        Y_train = df2['Risk_level']
        
        test_data_path = os.path.join(THIS_DIR, '..', 'sample_data/SVM_text_classifier/test_data.csv')
        df3 = pd.read_csv(test_data_path)
        X_test = df3['Synopsis']
        
        smodel = SVM_text_class(X_train,Y_train)
        Y_test = smodel.pred(X_test)

        self.assertEqual(Y_test.shape[0],150)
