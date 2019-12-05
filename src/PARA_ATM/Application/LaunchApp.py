"""
NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute (PI Dr. Yongming Liu)
@author: Michael Hartnett
@date: 07/19/2019

Run this module to invoke the application. It contains the main features and functions to execute the system.
"""

import os
from pathlib import Path

import psycopg2
import pandas as pd
import numpy as np

import bokeh as bk
import bokeh.layouts as bklayouts
import bokeh.models.widgets as bkwidgets
import bokeh.plotting as bkplot
from bokeh.models import ColumnDataSource
from bokeh.tile_providers import Vendors, get_provider
from bokeh.server.server import Server

from PARA_ATM.Commands.Helpers.DataStore import Access
from PARA_ATM.Commands import readNATS,readIFF,readTDDS
from .plotting_tools import merc
from .db_tools import getTableList,checkTable


# Variables for NATS and Sherlock directories
NATS_DIR = os.path.join(os.path.dirname(
    os.path.realpath(__file__)),'../../NATS/')
SHERLOCK_DIR = os.path.join(os.path.dirname(
    os.path.realpath(__file__)),'../../../data/Sherlock/')

#Set connection to postgres database based on the credentials mentioned
db_access = Access()
connection = db_access.connection
cursor = db_access.cursor

cmdpath = str(Path(__file__).parent.parent)+'/Commands/'

class Container:
    def __init__(self):

        self.cmdline = bkwidgets.TextInput()

        self.tableList = getTableList(cursor)
        self.tables = bkwidgets.Select(options=self.tableList,value=self.tableList[0])
        self.controls = bklayouts.widgetbox()

        #data source setup
        self.results = pd.DataFrame(columns=['id','time','callsign','latitude','longitude','heading','altitude','tas','param'])
        self.source = ColumnDataSource(self.results)
        self.source2 = ColumnDataSource(self.results)
        self.source3 = ColumnDataSource({'top':[],'bottom':[],'left':[],'right':[]})

        self.perf_results = None

        self.setup_layout()

    def setup_layout(self):

        #layout setup
        self.flights = bkwidgets.MultiSelect()
        tile_provider = get_provider(Vendors.CARTODBPOSITRON)
        p = bkplot.figure(x_axis_type='mercator', y_axis_type='mercator')
        p.add_tile(tile_provider)
        self.p2 = bkplot.figure()
        self.lines = self.p2.line(x='time',y='param',source=self.source2)
        self.hist = self.p2.quad(source=self.source3,top='top',bottom='bottom',left='left',right='right')
        self.params = bkwidgets.Select(options=['altitude','tas','fpf','performance_hist'],value='altitude')
        p2control=bklayouts.WidgetBox(self.params)
        layout = bklayouts.layout(self.controls,p)
        self.tables = bkwidgets.Select(options=self.tableList,value=self.tableList[0])
        self.time = bkwidgets.RangeSlider()
        self.populated = False

        #plot setup
        self.points = p.triangle(x='longitude',y='latitude',angle='heading',angle_units='deg',alpha=0.5,source=self.source)
        hover = bk.models.HoverTool()
        hover.tooltips = [ ("Callsign", "@callsign"), ("Time","@time"), ("Phase","@status"), ("Heading","@heading"), ("Altitude","@altitude"), ("Speed","@tas") ]
        hover2 = bk.models.HoverTool()
        hover2.tooltips = [ ("Callsign", "@callsign") ]
        self.p2.add_tools(hover2)
        p.add_tools(hover)

        #callback setup
        self.params.on_change('value',self.plot_param)
        self.tables.on_change('value',self.set_data_source)
        self.cmdline.on_change('value',self.runCmd)

        self.controls = bklayouts.row(bklayouts.WidgetBox(self.tables,self.cmdline),bk.models.Div(width=20),p2control)
        self.layout = bklayouts.column(self.controls,bklayouts.row(p,self.p2))        

    def set_data_source(self,attr,new,old):
        t = self.tables.value
        try:
            self.results = checkForTable(t)
        except:
            if os.path.exists(NATS_DIR+t):
                cmd = readNATS.Command(t)
            elif os.path.exists(SHERLOCK_DIR+t):
                cmd = readIFF.Command(t)
            else:
                cmd = readIFF.Command(t)
            self.results = cmd.executeCommand()[1]
            db_access.addTable(t,self.results)
            if os.path.exists(NATS_DIR+t):
                self.results['time'] = self.results['time'].astype('datetime64[s]').astype(int)
            else:
                self.results['time'] = self.results['time'].astype('datetime64[s]').astype('int')
        acids = np.unique(self.results['callsign']).tolist()
        times = sorted(np.unique(self.results['time']))
        self.flights = bkwidgets.MultiSelect(options=acids,value=[acids[0],])
        self.flights.on_change('value',self.update)
        self.time = bkwidgets.RangeSlider(title="time",value=(times[0],times[-1]),start=times[0],end=times[-1],step=1)
        self.time.on_change('value',self.update)
        if  self.populated:
            self.controls.children[1] = self.flights
            self.controls.children[2] = self.time
        else:
            self.controls.children.insert(1,self.flights)
            self.controls.children.insert(2,self.time)
            self.populated = True
        self.results['longitude'],self.results['latitude'] = merc(np.asarray(self.results['latitude'].astype(float)),np.asarray(self.results['longitude'].astype(float)))
        self.update('attr','new','old')

    def plot_param(self,attr,new,old):
        f = self.flights.value
        t = self.time.value
        param = self.params.value
        if param == 'performance_hist':
            data = self.perf_results
            counts, bins = np.histogram(data,density=True,bins=20)
            data = {'bottom':np.zeros(20),'top':counts,'left':bins[:-1],'right':bins[1:]}
            self.hist.data_source.data = data
        else:
            data = pd.DataFrame()
            data_dict = {'time':[],'callsign':[],'param':[]}
            within_time = np.logical_and(self.results['time']>=t[0],self.results['time']<=t[1])
            for i,acid in enumerate(f):
                data = data.append(self.results.loc[np.logical_and(self.results['callsign']==acid,within_time),['time','callsign',param]])
            data.columns=['time','callsign','param']
            data['time'] = (data['time'] - np.min(data['time']))/1e9
            self.lines.data_source.data = data.to_dict(orient='list')
            self.p2.xaxis.axis_label = 'time (s)'
            self.p2.yaxis.axis_label = param

    def update(self,attr,new,old):
        f = self.flights.value
        t = self.time.value
        data = pd.DataFrame()
        within_time = np.logical_and(self.results['time']>=t[0],self.results['time']<=t[1])
        for acid in f:
            data = data.append(self.results.loc[np.logical_and(self.results['callsign']==acid,within_time)])
        data['heading'] = data['heading'] - 90
        data.loc[data['heading']<0,'heading'] = data.loc[data['heading']<0,'heading'] + 360
        self.points.data_source.data = data.to_dict(orient='list')
        self.points.glyph.fill_color = bk.transform.factor_cmap('callsign',palette=bk.palettes.Category10[10],factors=f)
        self.points.glyph.line_color = bk.transform.factor_cmap('callsign',palette=bk.palettes.Category10[10],factors=f)
        self.plot_param(0,0,0)


    def runCmd(self,attr,old,new):
        commandInput = self.cmdline.value
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
            self.tables.value = commandArguments[0] if type(commandArguments)==list else commandArguments
            fpf_table = commandParameters[1]
            self.set_data_source('attr','new','old')
            for acid in np.unique(self.results['callsign']):
                self.results.loc[self.results['callsign']==acid,'fpf'] = fpf_table.loc[fpf_table['callsign']==acid,'fpf'].tolist()
            self.params.value = 'fpf'
            self.plot_param('attr','new','old')
        elif 'read' in commandName:
            self.tableList.append(commandArguments[0] if type(commandArguments)==list else commandArguments)
            self.tables.options=self.tableList
            self.tables.value = commandArguments[0] if type(commandArguments)==list else commandArguments
            db_access.addTable(self.tables.value)
            self.set_data_source('attr','old','new')
        elif 'run' in commandName:
            print(commandParameters)
            self.tables.value = commandParameters[1]
            self.set_data_source('attr','old','new')
        elif 'uncertainty' in commandName:
            print('Performance:\n',commandParameters[1])
            self.perf_results = commandParameters[1]
            self.params.value = 'performance_hist'
            self.plot_param(0,0,0)



def bkapp(doc):
    c = Container()
    doc.add_root(c.layout)


def main():
    print('Opening Bokeh application on http://localhost:5006/')
    server = Server({'/': bkapp})
    server.start()    

    server.io_loop.add_callback(server.show, "/")
    server.io_loop.start()    

if __name__ == '__main__':
    main()
