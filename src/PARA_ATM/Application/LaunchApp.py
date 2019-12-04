'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute (PI Dr. Yongming Liu)
@author: Michael Hartnett
@date: 07/19/2019

Run this module to invoke the application. It contains the main features and functions to execute the system.

'''
import subprocess
import os

def main():
    proc = subprocess.Popen(['bokeh', 'serve', __file__])
    os.system('python -mwebbrowser http://localhost:5006')
    os.system('kill %d'%proc.pid)
    quit()

if __name__ == '__main__':
    main()

import sys
import math
import glob
import time
from pathlib import Path
from itertools import product

import bokeh as bk
import bokeh.layouts as bklayouts
import bokeh.models.widgets as bkwidgets
import bokeh.plotting as bkplot
from bokeh.models import ColumnDataSource
from bokeh.tile_providers import Vendors, get_provider

#Question: Is this the best way to assign the pathing? Should we change the directory structure or the location of this application file to avoid this?
src_dir = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, src_dir)

from PARA_ATM import *
from PARA_ATM.Commands import readNATS,readIFF,readTDDS
from PARA_ATM.Application.plotting_tools import *
from PARA_ATM.Application.db_tools import *


# Variables for NATS and Sherlock directories
NATS_DIR = os.path.join(os.path.dirname(
    os.path.realpath(__file__)),'../../NATS/')
SHERLOCK_DIR = os.path.join(os.path.dirname(
    os.path.realpath(__file__)),'../../../data/Sherlock/')

#Set connection to postgres database based on the credentials mentioned
connection = psycopg2.connect(database="paraatm",
                              user="paraatm_user",
                              password="paraatm_user",
                              host="localhost",
                              port="5432")
cursor = connection.cursor()

#Todo: what to do with this? Is a global variable later?
perf_results = None

cmdpath = str(Path(__file__).parent.parent)+'/Commands/'


cmdline = bkwidgets.TextInput()

colors = ['blue','orange','green','red','purple','brown','pink','grey','olive','cyan']
tableList = getTableList(cursor)
tables = bkwidgets.Select(options=tableList,value=tableList[0])
controls = bklayouts.widgetbox()

#data source setup
results = pd.DataFrame(columns=['id','time','callsign','latitude','longitude','heading','altitude','tas','param'])
source = ColumnDataSource(results)
source2 = ColumnDataSource(results)
source3 = ColumnDataSource({'top':[],'bottom':[],'left':[],'right':[]})

def set_data_source(attr,new,old):
    global populated,controls,results,flights,time
    t = tables.value
    if os.path.exists(NATS_DIR+t):
        cmd = readNATS.Command(t)
    elif os.path.exists(SHERLOCK_DIR+t):
        cmd = readIFF.Command(t)
    else:
        cmd = readIFF.Command(t)
    results = cmd.executeCommand()[1]
    if os.path.exists(NATS_DIR+t):
        results['time'] = results['time'].astype('datetime64[s]').astype(int)
    else:
        results['time'] = results['time'].astype('datetime64[s]').astype('int')
    acids = np.unique(results['callsign']).tolist()
    times = sorted(np.unique(results['time']))
    flights = bkwidgets.MultiSelect(options=acids,value=[acids[0],])
    flights.on_change('value',update)
    time = bkwidgets.RangeSlider(title="time",value=(times[0],times[-1]),start=times[0],end=times[-1],step=1)
    time.on_change('value',update)
    if  populated:
        controls.children[1] = flights
        controls.children[2] = time
    else:
        controls.children.insert(1,flights)
        controls.children.insert(2,time)
        populated = True
    results['longitude'],results['latitude'] = merc(np.asarray(results['latitude'].astype(float)),np.asarray(results['longitude'].astype(float)))
    update('attr','new','old')

def plot_param(attr,new,old):
    f = flights.value
    t = time.value
    param = params.value
    if param == 'performance_hist':
        data = perf_results
        counts, bins = np.histogram(data,density=True,bins=20)
        data = {'bottom':np.zeros(20),'top':counts,'left':bins[:-1],'right':bins[1:]}
        hist.data_source.data = data
    else:
        data = pd.DataFrame()
        data_dict = {'time':[],'callsign':[],'param':[]}
        within_time = np.bitwise_and(results['time']>=t[0],results['time']<=t[1])
        for i,acid in enumerate(f):
            data = data.append(results.loc[np.bitwise_and(results['callsign']==acid,within_time),['time','callsign',param]])
        data.columns=['time','callsign','param']
        data['time'] = (data['time'] - np.min(data['time']))/1e9
        lines.data_source.data = data.to_dict(orient='list')
        p2.xaxis.axis_label = 'time (s)'
        p2.yaxis.axis_label = param

def update(attr,new,old):
    f = flights.value
    t = time.value
    data = pd.DataFrame()
    within_time = np.bitwise_and(results['time']>=t[0],results['time']<=t[1])
    for acid in f:
        data = data.append(results.loc[np.bitwise_and(results['callsign']==acid,within_time)])
    data['heading'] = data['heading'] - 90
    data.loc[data['heading']<0,'heading'] = data.loc[data['heading']<0,'heading'] + 360
    points.data_source.data = data.to_dict(orient='list')
    points.glyph.fill_color = bk.transform.factor_cmap('callsign',palette=bk.palettes.Category10[10],factors=f)
    points.glyph.line_color = bk.transform.factor_cmap('callsign',palette=bk.palettes.Category10[10],factors=f)
    plot_param(0,0,0)


def runCmd(attr,old,new):
    global tables,tableList
    commandInput = cmdline.value
    commandName = str(commandInput.split('(')[0])
    cmd = getattr(__import__('PARA_ATM.Commands',fromlist=[commandName]), commandName)
    commandArguments = '('.join(commandInput.split('(')[1:])[:-1]
    if ',' in commandArguments:
        commandArguments = commandArguments.split(',') 
    print(commandArguments)
    commandClass = cmd.Command(commandArguments)
    commandParameters = commandClass.executeCommand()
    print('command %s executed'%commandName)
    if commandName=='groundSSD':
        global results
        tables.value = commandArguments[0] if type(commandArguments)==list else commandArguments
        fpf_table = commandParameters[1]
        set_data_source('attr','new','old')
        for acid in np.unique(results['callsign']):
            results.loc[results['callsign']==acid,'fpf'] = fpf_table.loc[fpf_table['callsign']==acid,'fpf'].tolist()
        params.value = 'fpf'
        plot_param('attr','new','old')
    elif 'read' in commandName:
        tableList.append(commandArguments[0] if type(commandArguments)==list else commandArguments)
        tables.options=tableList
        tables.value = commandArguments[0] if type(commandArguments)==list else commandArguments
        set_data_source('attr','old','new')
    elif 'run' in commandName:
        print(commandParameters)
        tables.value = commandParameters[1]
        set_data_source('attr','old','new')
    elif 'uncertainty' in commandName:
        global perf_results
        print('Performance:\n',commandParameters[1])
        perf_results = commandParameters[1]
        params.value = 'performance_hist'
        plot_param(0,0,0)


#layout setup
flights = bkwidgets.MultiSelect()
tile_provider = get_provider(Vendors.CARTODBPOSITRON)
p = bkplot.figure(x_axis_type='mercator', y_axis_type='mercator')
p.add_tile(tile_provider)
p2 = bkplot.figure()
lines = p2.line(x='time',y='param',source=source2)
hist = p2.quad(source=source3,top='top',bottom='bottom',left='left',right='right')
params = bkwidgets.Select(options=['altitude','tas','fpf','performance_hist'],value='altitude')
p2control=bklayouts.WidgetBox(params)
layout = bklayouts.layout(controls,p)
tables = bkwidgets.Select(options=tableList,value=tableList[0])
time = bkwidgets.RangeSlider()
populated = False

#plot setup
points = p.triangle(x='longitude',y='latitude',angle='heading',angle_units='deg',alpha=0.5,source=source)
hover = bk.models.HoverTool()
hover.tooltips = [ ("Callsign", "@callsign"), ("Time","@time"), ("Phase","@status"), ("Heading","@heading"), ("Altitude","@altitude"), ("Speed","@tas") ]
hover2 = bk.models.HoverTool()
hover2.tooltips = [ ("Callsign", "@callsign") ]
p2.add_tools(hover2)
p.add_tools(hover)

#callback setup
params.on_change('value',plot_param)
tables.on_change('value',set_data_source)
cmdline.on_change('value',runCmd)

controls = bklayouts.row(bklayouts.WidgetBox(tables,cmdline),bk.models.Div(width=20),p2control)
layout = bklayouts.column(controls,bklayouts.row(p,p2))
bk.io.curdoc().add_root(layout)
