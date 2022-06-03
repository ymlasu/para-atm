#! /usr/bin/python3 python3
# -*- coding: utf-8 -*-

"""
@Author: Jiawei Chen
@Date: 2020-05-20
This Python script is used for HPMM (Human Performance Monitoring Module)
The script outputs predicted loss of separation as an indicator of air traffic controller's performance
The script can also check compliance for each command
@Last Modified by: Jiawei Chen
@Last Modified date: 2020-05-26
"""
from typing import Any, Union

from jpype import *
from array import *
import pandas as pd
import numpy as np
import scipy.stats as sts
import os
import time
import sys
import datetime
from shutil import copyfile
from shutil import rmtree

import matplotlib.pyplot as plt
from pandas import Series, DataFrame
from pandas.io.parsers import TextFileReader
from scipy.stats import norm
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import catboost as cb
from catboost import CatBoostRegressor
from catboost import Pool



class HPMM(object):
    def __init__(self, cfg):
        self.data = pd.read_csv(cfg['datafile']);

    def preprocessing(self):
        # according to experiment design, remove redundant variables
        data = self.data
        data_domain = data.drop(
            columns=['Ss', 'condtn', 'los_dur_over5min', 'query_timed_out', 'ready_timed_out', 'ready_latency_adj',
                     'cum_los_dur',
                     'stimuli', 'response_text', 'condtn_num'])
        # fill in missing values
        data_domain['sa_correct'].fillna(data_domain['sa_correct'].mode()[0], inplace=True)
        data_domain.fillna(data_domain.mean(), inplace=True)

        # transform categorical data
        data_domain = data_domain.join(pd.get_dummies(data_domain.sa_correct))
        data_domain = data_domain.join(pd.get_dummies(data_domain['query']))
        data_domain = data_domain.drop(columns=['query', 'sa_correct'])
        return data_domain

    def modelpredict(model, input):
        return model.predict(input)

    def train(self, model, train_pool, test_pool, plot):
        model.fit(train_pool, eval_set=test_pool, plot=plot)


if __name__ == '__main__':
    # my code
    cfg = {
        'datafile': '/home/jchen311/para-atm/paraatm/sample_data/human_data.csv'
    }
    hpmm = HPMM(cfg)
    data = hpmm.preprocessing()
    X = data.drop(columns=['los_freq'])
    Y = data['los_freq']
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=10)
    model = CatBoostRegressor()
    train_pool = Pool(X_train, y_train)
    test_pool = Pool(X_test, y_test)
    grid = {'learning_rate': [0.01, 0.05, 0.1],
            'depth': [4, 6, 10],
            'l2_leaf_reg': [1, 3, 5, 7, 9],
            }

    grid_search_result = model.grid_search(grid, X=X_train, y=y_train, cv=3, plot=True)
    # choose parameters based on grid_search results
    model = CatBoostRegressor(
        iterations=1000,
        depth=6,
        learning_rate=0.1,
        l2_leaf_reg=3,
        loss_function='RMSE',
        eval_metric='R2',
        random_seed=1234
    )
    model.fit(train_pool, eval_set=test_pool, plot=True)
    preds = model.predict(test_pool)
    print(preds)
    model.save_model("catboost")
