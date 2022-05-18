import pandas as pd
import numpy as np
import pickle
from catboost import CatBoostClassifier
from sklearn.linear_model import LogisticRegression

class LosModel():
    def __init__(self,model_name,model_type='catboost'):
        self.model_type=model_type

        if self.model_type == 'catboost':
            self.model = CatBoostClassifier()
            self.model.load_model(model_name)

        if self.model_type == 'LogisticRegression':
            self.model = pickle.load(open(model_name,'rb'))

    def __call__(self,x):
        if self.model_type == 'catboost':
            y=self.model.predict(x)

        if self.model_type == 'LogisticRegression':
            y = self.model.predict(x)

        return(y)
        