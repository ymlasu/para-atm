'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute (PI Dr. Yongming Liu)
@author: Michael Hartnett
@date: 07/19/2019

Run this module to invoke the application. It contains the main features and functions to execute the system.

'''

import sys

sys.path.insert(0, '/home/edecarlo/dev/nasa-uli/src/')

from NATS.Client import *
from PARA_ATM import *
from PARA_ATM.Commands import readNATS,readIFF,readTDDS
from bokeh.io import output_file, show, curdoc
from bokeh.layouts import row,column,WidgetBox,layout
from bokeh.models import CategoricalColorMapper, Div, HoverTool, ColumnDataSource, Panel, CustomJS
from bokeh.models.widgets import MultiSelect, Select, Slider, RangeSlider, TextInput, AutocompleteInput
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import components
from bokeh.tile_providers import get_provider, Vendors
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.transform import factor_cmap
from bokeh.palettes import Category10
from itertools import product
import time
import math
import glob

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

def inverse_merc(y):
    r_major = 6378137.
    lats = 360/math.pi * np.arctan(np.exp(y/r_major)) - 90.
    return lats


NATS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../NATS/Server/')
SHERLOCK_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../../../data/Sherlock/')
#Set connection to postgres database based on the credentials mentioned
connection = psycopg2.connect(database="paraatm", user="paraatm_user", password="paraatm_user", host="localhost", port="5432")
cursor = connection.cursor()

cmdpath = str(Path(__file__).parent.parent)+'/Commands/'

def getTableList():

    #Execute query to fetch flight data
    query = "SELECT t.table_name \
             FROM information_schema.tables t \
             JOIN information_schema.columns c ON c.table_name = t.table_name \
             WHERE c.column_name LIKE 'callsign'"
    cursor.execute(query)
    results = cursor.fetchall()
    return [result[0] for result in results]

def getCmdList():
    cmdlist = [cmd.split('/')[-1].split('.')[0] for cmd in glob.glob(cmdpath+'*.py')]
    return cmdlist 

cmdline = TextInput()
#permute = [a+'('+b+')'for a,b in product(getCmdList(),getTableList())]
#cmdline = AutocompleteInput(completions=permute)
#cmdline = AutocompleteInput(completions=['readNATS(TRX_DEMO_SFO_PHX_new_G2G_output.csv)','groundSSD(incident)','uncertaintyProp(groundSSD(incident))'])

colors = ['blue','orange','green','red','purple','brown','pink','grey','olive','cyan']
tableList = getTableList()
tables = Select(options=tableList,value=tableList[0])
controls = WidgetBox()

#data source set up
results = pd.DataFrame(columns=['id','time','callsign','latitude','longitude','heading','altitude','tas','param'])
source = ColumnDataSource(results)
source2 = ColumnDataSource(results)
source3 = ColumnDataSource({'top':[],'bottom':[],'left':[],'right':[]})

#layout setup
flights = MultiSelect()
tile_provider = get_provider(Vendors.CARTODBPOSITRON)
p = figure(x_axis_type='mercator', y_axis_type='mercator')
p.add_tile(tile_provider)
p2 = figure()
lines = p2.line(x='time',y='param',source=source2)
hist = p2.quad(source=source3,top='top',bottom='bottom',left='left',right='right')
params = Select(options=['altitude','tas','fpf','lat_hist'],value='lat_hist')
p2control=WidgetBox(params)
layout = layout(controls,p)
tables = Select(options=tableList,value=tableList[0])
time = RangeSlider()
populated = False

points = p.triangle(x='longitude',y='latitude',angle='heading',angle_units='deg',alpha=0.5,source=source)
hover = HoverTool()
hover.tooltips = [ ("Callsign", "@callsign"), ("Time","@time"), ("Phase","@status"), ("Heading","@heading"), ("Altitude","@altitude"), ("Speed","@tas") ]
hover2 = HoverTool()
hover2.tooltips = [ ("Callsign", "@callsign") ]
p2.add_tools(hover2)
p.add_tools(hover)

def plot_param(attr,new,old):
    f = flights.value
    t = time.value
    param = params.value
    if param == 'lat_hist':
        data = []
        within_time = np.bitwise_and(results['time']>=t[0],results['time']<=t[1])
        for i,acid in enumerate(f):
            data.append(inverse_merc(np.array(results.loc[np.bitwise_and(results['callsign']==acid,within_time),['latitude']])))
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
    points.glyph.fill_color = factor_cmap('callsign',palette=Category10[10],factors=f)
    points.glyph.line_color = factor_cmap('callsign',palette=Category10[10],factors=f)
    plot_param(0,0,0)

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
    flights = MultiSelect(options=acids,value=[acids[0],])
    flights.on_change('value',update)
    time = RangeSlider(title="time",value=(times[0],times[-1]),start=times[0],end=times[-1],step=1)
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

def runCmd(old,new,attr):
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

#callback setup
params.on_change('value',plot_param)
tables.on_change('value',set_data_source)
cmdline.on_change('value',runCmd)

def index():
    global controls
    controls = row(WidgetBox(tables,cmdline),Div(width=20),p2control)
    layout = column(controls,row(p,p2))
    curdoc().add_root(layout)

index()
