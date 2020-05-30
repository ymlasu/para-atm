import pandas as pd
import numpy as np
import os
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
name=list(range(0,40))
df = pd.read_csv('IFF_ASU.csv',usecols=[*range(0,40)],header=None,skiprows=[*range(0,3)],
                     engine='python',names=name)
df = df.drop([3,4,5,6,8,13,14,15,19,21,22,24,25,26,27,28,29,30,31,32,33,34,35,37,38],axis=1)
df.columns = ['tag','time_stamp','daily_num',
              'call_sign','latitude','longitude',
              'height','operation','ground_speed',
              'course','rate_of_climb',
              'performance','approch_rwy',
              'D_airport','reg_num']
daily_names = df['daily_num'].unique().tolist()
df = df.fillna('NONE')
df2 = pd.DataFrame(daily_names)
df = df.replace('?','NONE')
df2[0] = df2[0].apply(str)
df.to_csv('IFF_2020.csv',index=False,header=None)
df2.to_csv('IFF_2020_dailynums.csv',index=False,header=None)
