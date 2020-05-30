import pandas as pd
import numpy as np

file = pd.read_csv('summary_usefuldata.csv')

df_Arrive = file[file['operation']=='A']

df_Departure = file[file['operation']=='D']


Avg_Speed = file['avg_ground_speed'].mean()
Std_Speed = file.loc[:,'avg_ground_speed'].std()

Arrive_Avg_Speed=df_Arrive['avg_ground_speed'].mean()
Arrive_Std_speed = df_Arrive.loc[:,'avg_ground_speed'].std()

Departure_Avg_Speed = df_Departure['avg_ground_speed'].mean()
Departure_Std_speed = df_Departure.loc[:,'avg_ground_speed'].std()

data = {'Average_Speed': [Avg_Speed], 'Standard_Deviation_of_Speed': [Std_Speed],
        'Arrival_Average_Speed': [Arrive_Avg_Speed], 'Standard_Deviation_of_Arrival_Speed': [Arrive_Std_speed],
        'Departure_Average_Speed':[Departure_Avg_Speed],'Standard_Deviation_of_Departure_Speed':[Departure_Std_speed]}
output_df = pd.DataFrame(data)
output_df.to_csv('ASDE-X_Speed.csv',index=False)