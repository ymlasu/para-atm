from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats

import sys
sys.path.append('./Helpers/')
import DataStore

#add to database
engine = create_engine('postgresql://paraatm_user:paraatm_user@localhost:5432/paraatm')

results = pd.DataFrame([['norm','4,1','nominal']],columns=['type','params','state'])
tablename = 'atc_uncertainty'

try:
    results.to_sql(tablename, engine)
except:
    print('Table already exists')

subject = 'atc'
state = 'nominal'

db_access = DataStore.Access()

dist_type,loc,scale,args = db_access.getReaction(subject,state)
dist_type = 'norm'

dist = getattr(scipy.stats,dist_type)
print(args,loc,scale)

x = np.linspace(3,5,100)

pdf = dist(*args,loc=loc,scale=scale).pdf(x)
plt.plot(pdf)
plt.show()

