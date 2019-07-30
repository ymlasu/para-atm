'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

Run this module to invoke the application. It contains the main features and functions to execute the system.

'''

import sys

sys.path.insert(0, '/home/dyn.datasys.swri.edu/mhartnett/NASA_ULI/NASA_ULI_InfoFusion/src/')

from PARA_ATM import *
from PARA_ATM.Commands import readNATS,readIFF,readTDDS
from bokeh.io import output_file, show, curdoc
from bokeh.layouts import column,WidgetBox,layout
from bokeh.models import CategoricalColorMapper, Div, HoverTool, ColumnDataSource, Panel, CustomJS
from bokeh.models.widgets import MultiSelect, Select, Slider, RangeSlider
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import components
from bokeh.tile_providers import get_provider, Vendors
from bokeh.plotting import figure
from bokeh.server.server import Server
from flask import Flask, render_template, request
from itertools import repeat
import time
import math

def merc(lats,lons):
    coords_xy = ([],[])
    for i in range(len(lats)):
        r_major = 6378137.0
        x = r_major * math.radians(lons[i])
        scale = x/lons[i]
        y = 180./math.pi * math.log(math.tan(math.pi/4 + lats[i] * (math.pi/180)/2)) * scale
        coords_xy[0].append(x)
        coords_xy[1].append(y)
    return coords_xy


NATS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../NATS/Server/')
SHERLOCK_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../../data/Sherlock/')
#Set connection to postgres database based on the credentials mentioned
connection = psycopg2.connect(database="paraatm", user="paraatm_user", password="paraatm_user", host="localhost", port="5432")
cursor = connection.cursor()

def getTableList():

    #Execute query to fetch flight data
    query = "SELECT t.table_name \
             FROM information_schema.tables t \
             JOIN information_schema.columns c ON c.table_name = t.table_name \
             WHERE c.column_name LIKE 'callsign'"
    cursor.execute(query)
    results = cursor.fetchall()
    return [result[0] for result in results]

tableList = getTableList()
tables = Select(options=tableList,value=tableList[0])
controls = WidgetBox()
results = pd.DataFrame(columns=['time','latitude','longitude','heading','altitude','tas'])
source = ColumnDataSource(results)
flights = MultiSelect()
tile_provider = get_provider(Vendors.CARTODBPOSITRON)
p = figure(x_axis_type='mercator', y_axis_type='mercator')
p.add_tile(tile_provider)
layout = layout(controls,p)
tables = Select(options=tableList,value=tableList[0])
time = RangeSlider()
populated = False

points = p.triangle(x='longitude',y='latitude',angle='heading',angle_units='deg',source=source)
lines = p.multi_line(xs='longitude',ys='latitude',source=source)
hover = HoverTool()
hover.tooltips = [ ("Callsign", "@callsign"), ("Time","@time"), ("Phase","@status"), ("Heading","@heading"), ("Altitude","@altitude"), ("Speed","@tas") ]
p.add_tools(hover)

def update(attr,new,old):
    f = flights.value
    t = time.value
    data = pd.DataFrame()
    for acid in f:
        within_time = np.bitwise_and(results['time']>=t[0],results['time']<=t[1])
        data = data.append(results.loc[np.bitwise_and(results['callsign']==acid,within_time)])
    data['heading'] = data['heading'] - 90
    data.loc[data['heading']<0,'heading'] = data.loc[data['heading']<0,'heading'] + 360
    points.data_source.data = data.to_dict(orient='list')
    lines.data_source.data = data.to_dict(orient='list')

def set_data_source(attr,new,old):
    global populated,controls,results,flights,time
    t = tables.value
    if os.path.exists(NATS_DIR+t):
        cmd = readNATS.Command(cursor,t)
    elif os.path.exists(SHERLOCK_DIR+t):
        cmd = readIFF.Command(cursor,t)
    else:
        cmd = readIFF.Command(cursor,t)
    results = cmd.executeCommand()[1]
    if os.path.exists(NATS_DIR+t):
        results['time'] = results['time'].astype(float)
    else:
        results['time'] = results['time'].astype('datetime64[s]').astype('int')
    acids = np.unique(results['callsign']).tolist()
    times = sorted(np.unique(results['time']).tolist())
    flights = MultiSelect(options=acids,value=[acids[0],])
    flights.on_change('value',update)
    time = RangeSlider(title="time",value=(times[0],times[-1]),start=times[0],end=times[-1],step=10,callback_policy='mouseup')
    time.on_change('value',update)
    if  populated:
        controls.children[1] = flights
        controls.children[2] = time
    else:
        controls.children.insert(1,flights)
        controls.children.insert(2,time)
        populated = True
    results['longitude'],results['latitude'] = merc(results['latitude'].astype(float),results['longitude'].astype(float))

tables.on_change('value',set_data_source)

def index():
    global controls
    controls = WidgetBox(tables)
    layout = column(controls,p)
    curdoc().add_root(layout)

index()
