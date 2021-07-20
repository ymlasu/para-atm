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


class SVM_text_class(object):
    """
    SVM_text_class creates SVM classifier and predicts class for the input text data 
    
    Methods:
    -------
    _get_SVM_model
    pred

    Parameters
    ----------
    x_train : array
        1D array of training input values
    y_train : array
        1D array of training output values
   
    """
    def __init__(self,x_train,y_train):
        self.x_train = x_train
        self.y_train = y_train
        self.svm = self._get_svm_model()
        self.svm.fit(self.x_train,self.y_train)

    def _get_svm_model(self):

        text_clf = Pipeline([('vect', CountVectorizer(stop_words = 'english')),
                          ('tfidf', TfidfTransformer()),
                          ('clf', SGDClassifier(loss='epsilon_insensitive', penalty='l2',
                                                alpha=1e-5, random_state=40,
                                                max_iter=10, tol=None)),
                        ])
        optimal_parameters = {'vect__ngram_range':  [(1, 2)],
                              'tfidf__use_idf': [True],
                              'clf__loss': ['modified_huber'],
                              'clf__alpha': [1e-5],
                              'clf__penalty': ['elasticnet'],
                              'clf__max_iter': [80],
                  }

        gs_clf = GridSearchCV(text_clf, optimal_parameters, n_jobs=-1,cv = 5)        
        return gs_clf

    def pred(self, x):
        return self.svm.predict(x)
