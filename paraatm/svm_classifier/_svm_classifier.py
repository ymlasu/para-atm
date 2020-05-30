# -*- coding: utf-8 -*-
"""
Created on Thu May 28 08:49:23 2020

@author: karvepm
"""
"""
Support vector machine, multi-class, classifier for text data
---
Required pakages:
Pipeline
sklearn
"""
from sklearn.pipeline import Pipeline
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer


class SVM_ASRS_risk_category(object):
    """
    SVM class creates SVM classifier and predicts class for the input text data 
    
    ----------
    x_train: training input
    y_train: training target
    x_test: testing input
    
    Methods:
    -------
    get_SVM_model
        
    """
    def __init__(self,x_train,y_train):
        self.x_train = x_train
        self.y_train = y_train

    def get_risk_category(self,x_test):

        text_clf = Pipeline([('vect', CountVectorizer(stop_words = 'english')),
                          ('tfidf', TfidfTransformer()),
                          ('clf', SGDClassifier(loss='epsilon_insensitive', penalty='l2',
                                                alpha=1e-5, random_state=40,
                                                max_iter=10, tol=None)),
                        ])
        optimal_parameters = {'clf__loss': ['modified_huber'],
                  'vect__ngram_range':  [(1, 2)],
                  'tfidf__use_idf': [True],
                  'clf__alpha': [1e-5],
                  'clf__penalty': ['elasticnet'],
                  'clf__max_iter': [80],
                  }

        gs_clf = GridSearchCV(text_clf, optimal_parameters, n_jobs=-1,cv = 5)
        gs_clf.fit(self.x_train, self.y_train)
        
        results=gs_clf.predict(x_test)
        return results
