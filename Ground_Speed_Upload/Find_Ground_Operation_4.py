import pandas as pd
import numpy as np
import time as tm
import csv
import shutil
import os
import re



def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

Ground_Aircraft = "2020groundAircraft"
createFolder('./' + str(Ground_Aircraft) + '/')


files_location = os.path.join(os.getcwd(),"2020Aircraft")
for info in os.listdir(files_location):
    domain = os.path.abspath(files_location)
    infoo = os.path.join(domain, info)
    df = pd.read_csv(infoo)
    a = np.array(df['height'].values.tolist())
    df['height'] = np.where(a < 1.13, 1.13, a).tolist()
    df = df[df['height']==1.13]

    # Select Particular Range's data

    # df = df[(df['latitude']>33.948322)&(df['latitude']<33.948646)]
    # df = df[(df['longitude']>-118.409239)&(df['longitude']<-118.40602)]

    df = df.reset_index(drop=True)
    # row_num = int(df['height'].count())
    # row_num = row_num+1
    # insert = range(0, row_num)
    df['time_second'] = df.index



    df.to_csv("2020groundAircraft/" + info, index=False)
