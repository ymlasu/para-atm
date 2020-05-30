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

Distinguished_All_Move = "2020csvcsv"
createFolder('./' + str(Distinguished_All_Move) + '/')

Distinguished_Aircraft = "2020Aircraft"
createFolder('./' + str(Distinguished_Aircraft) + '/')

files_location = os.path.join(os.getcwd(),"2020csvcsv")
i = -1
for info in os.listdir(files_location):

    domain = os.path.abspath(files_location)
    infoo = os.path.join(domain, info)

    df = pd.read_csv(infoo)
    A = str(df.loc[0,'call_sign'])
    pattern = re.compile("^[A-Z]{3}\d+")

    print(A)
    if pattern.match(A):
        i = i + 1
        filename = str(i).zfill(4)
        shutil.copy(infoo,os.path.join(os.getcwd(),"2020Aircraft",filename+".csv"))

