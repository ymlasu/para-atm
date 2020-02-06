from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats

import sys
sys.path.append('./Helpers/')
sys.path.insert(0, '/home/dyn.datasys.swri.edu/mhartnett/NASA_ULI/NASA_ULI_InfoFusion/src/')
import paraatm
from sys import argv
import DataStore

#Entered by user
cmdName = argv[1]
db_file = argv[2]
subject_list = ['atc','pilot','vehicle']
state_list = ['nominal']
Nsamples = 10000

db_access = DataStore.Access()

dist_objs = [db_access.getCentaurDist(subject,state) for subject in subject_list for state in state_list]
print(dist_objs)


#Create random variable
rv_vector = np.array([np.array(dist.sample(Nsamples)) for dist in dist_objs]).reshape(3,-1)
print(rv_vector)

#propagate
mod = getattr(paraatm.Commands,cmdName).Command
results = [mod(db_file,rv).executeCommand() for rv in rv_vector]
print(results)

