import pandas as pd
import numpy as np
import time as tm
import csv
import shutil
import os
import re
from geopy import distance


def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)



Final_Aircraft = "2020finalcsv"
createFolder('./' + str(Final_Aircraft) + '/')



# pd.set_option('display.max_columns', None)
# pd.set_option('display.precision',9)
files_location = os.path.join(os.getcwd(),"2020groundAircraft")
df2= pd.DataFrame(columns = ['time_stamp','time_second',
              'airline','operation','avg_ground_speed','avg_dif_course',
              'performance','approch_rwy',
              'D_airport','sum_distance'])
num = -1
for info in os.listdir(files_location):
    print(info)
    domain = os.path.abspath(files_location)
    infoo = os.path.join(domain, info)
    df = pd.read_csv(infoo)
    if df.shape[0]==0:
        continue
    split = df['call_sign'].str.split('([A-Za-z]+)(\d+)', expand=True)
    split = split.loc[:, [1, 2]]
    split.rename(columns={1: 'airline', 2: 'call_nums'}, inplace=True)
    df = pd.concat([df, split], axis=1,sort=False)

    avg_groundspeed = df['ground_speed'].mean()
    df['avg_ground_speed'] = avg_groundspeed

    df['dif_course'] = df['course'].diff().abs()
    avg_dif_course = df['dif_course'].mean()
    df['avg_dif_course']=avg_dif_course

    df['latitude'] = df['latitude'].astype(np.float)
    df['longitude'] =df['longitude'].astype(np.float)
    df['distance']=''
    for d in range(0, df.shape[0]-1):
        d1=d+1

        df.loc[d1, 'distance'] = distance.distance(df.loc[d, ['latitude','longitude']], df.loc[d1, ['latitude','longitude']]).m
    df.loc[0,'distance']=0
    sum_distance = df['distance'].sum()
    df['sum_distance'] = sum_distance

    num = num +1
    filename = str(num).zfill(4)
    df.to_csv('2020finalcsv/'+str(filename)+'.csv',index=False)

    df = df.drop(['dif_course', 'course','call_sign',
                  'daily_num', 'height', 'rate_of_climb', 'reg_num',
                  'ground_speed','distance','latitude', 'longitude','call_nums'], axis=1)
    df = df[-1:]

    df2 = pd.concat([df2,df],sort=False)
    df2 = df2.reset_index(drop=True)
df2.to_csv('summary_usefuldata.csv',index=False)
# print(df2)