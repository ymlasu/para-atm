import pandas as pd
import numpy as np
import time as tm
import csv
import shutil
import os
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)
# pd.set_option('display.precision',9)
files_location = os.path.join(os.getcwd(),"2020csv")
num=-1
for info in os.listdir(files_location):
    print(info)

    domain = os.path.abspath(files_location)
    infoo = os.path.join(domain, info)

    df = pd.read_csv(infoo,header=None)

    df.columns=['tag','time_stamp','daily_num',
              'call_sign','latitude','longitude',
              'height','operation','ground_speed',
              'course','rate_of_climb',
              'performance','approch_rwy',
              'D_airport','reg_num']
    if df['tag'].astype(str).str.contains('3').any()  and df['tag'].astype(str).str.contains('4').any() :



        df['operation'] = df.loc[0,'operation']
        filter1 = df['tag']==4
        filter2 = df['performance']!='NONE'
        filter = df['performance'].where(filter1&filter2).dropna()
        df['performance'] = filter[1]
        if not df['reg_num'].astype(str).str.contains('NONE').all():
            reg_num_index = df[df['reg_num']!='NONE'].index[0]
            df['reg_num'] = df.loc[reg_num_index,'reg_num']
        else:
            num = num +1
            df['reg_num'] = "UNKW"+str(num)
        df = df.reset_index(drop=True)
        if df.loc[0,'operation'] =='A':
            df['approch_rwy'] = df['approch_rwy'].replace('unassigned','NONE')
            if not df['approch_rwy'].astype(str).str.contains('NONE').all():
                Arwy_index = df[df['approch_rwy'] != 'NONE'].index[0]
                df['approch_rwy'] = df.loc[Arwy_index, 'approch_rwy']
            else:
                df['approch_rwy'] = 'A_NoARwy'
        else:
            df['approch_rwy'] = 'No_ARwy'
        if df.loc[0,'operation'] =='D':
            if not df['D_airport'].astype(str).str.contains('NONE').all():
                D_index = df[df['D_airport'] != 'NONE'].index[0]
                df['D_airport'] = df.loc[D_index, 'D_airport']
            else:
                df['D_airport'] = 'D_NoDAirport'
        else:
            df['D_airport'] = 'ASU'
        df = df[df['tag']==3]
        df = df.reset_index(drop=True)
        df = df.drop('tag',axis=1)

        ###Linear interpolation
        for i in range(0,60):
            i=i+1
            df2 = (df['time_stamp'].diff() > 1).shift(-1).fillna(False)
            if not df2.all() is False:
                idx = df2[df2].index
                if not idx.empty:
                    start = int(df.loc[idx[0],'time_stamp'])

                    e_id = idx[0]+1
                    end = int(df.loc[e_id,'time_stamp'])
                    insert = range(start+1,end)
                    df_extra=pd.DataFrame({'time_stamp':insert})
                    # print(df_extra)
                    insertion_point = idx[0]+1
                    df = pd.concat([df.iloc[:insertion_point], df_extra, df.iloc[insertion_point:]],sort=True).reset_index(drop=True)
        df = df.sort_values('time_stamp').reset_index(drop=True)
        df['height']= df.interpolate(method='linear')['height'].bfill()
        df['ground_speed'] = df.interpolate(method='linear')['ground_speed'].bfill()
        df['course'] = df.interpolate(method='linear')['course'].bfill()
        df['latitude'] = df.interpolate(method='linear')['latitude'].bfill()
        df['longitude'] = df.interpolate(method='linear')['longitude'].bfill()
        df['rate_of_climb'] = df.interpolate(method='linear')['rate_of_climb'].bfill()
        df['operation'] = df.loc[0, 'operation']
        df['performance'] = df.loc[0, 'performance']
        df['call_sign'] = df.loc[0, 'call_sign']
        df['D_airport'] = df.loc[0, 'D_airport']
        df['approch_rwy'] = df.loc[0, 'approch_rwy']
        df['daily_num'] = df.loc[0, 'daily_num']
        df['reg_num'] = df.loc[0, 'reg_num']
        df.to_csv("2020csvcsv/"+info,index=False)
    # else:
    #     os.remove(infoo)





