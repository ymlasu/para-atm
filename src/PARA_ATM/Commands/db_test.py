from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats

import sys
sys.path.append('./Helpers/')
import DataStore

#Entered by user
func = getattr('PARA_ATM.Commands',argv[1])
db_file = argv[2]
subject_list = ['atc']
state_list = ['nominal']
Nsamples = 10000

db_access = DataStore.Access()

dist_objs = [db_access.getCentaurDist(subject,state) for subject in subject_list for state in state_list]

#Create random variable
rv_vector = np.array([np.array(dist.sample(Nsamples)) for dist in dist_objs])

#propagate
results = rv_vector.apply(lambda x: return func(db_file,x))


