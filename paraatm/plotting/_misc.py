import numpy as np
import math

import bokeh as bk
import bokeh.plotting as bkplot
from bokeh.models import HoverTool
from bokeh.tile_providers import Vendors, get_provider

def plot_trajectory(df, output_file=None, output_notebook=False, plot_width=1200, plot_height=600, tooltips=False, tile_provider=Vendors.STAMEN_TERRAIN):
    """Plot scenario trajectory to static html and open browser
    
    Parameters
    ----------
    df : DataFrame or GeoDataFrame
        DataFrame containing a scenario with 'latitude', 'longitude',
        'heading', and 'callsign' columns (DataFrame) or a defined geometry, 
        'heading', and 'callsign' (GeoDataFrame)
    output_file : str
        Output file for html (if None, use bokeh default)
    output_notebook : bool
        If True, output to jupyter notebook
    plot_width : int
        Plot width in screen units
    plot_height : int
        Plot height in screen units
    tooltips : bool
        Whether to include tooltips that display information when
        hovering over the data points
    tile_providers : str or Vendors enum
        The bokeh "tile provider" used to draw the map background.
        May be either a string or an instance of the
        `bokeh.tile_providers.Vendors` enum.  See also
        :py:func:`get_tile_providers`.
    """
    if output_file is not None:
        bkplot.output_file(output_file)
    elif output_notebook:
        bkplot.output_notebook()

    hover = HoverTool(
        tooltips = [
            ('Callsign','@callsign')
        ]
    )

    p = bkplot.figure(x_axis_type='mercator', y_axis_type='mercator', plot_width=plot_width, plot_height=plot_height)
    p.add_tile(get_provider(tile_provider))
    if tooltips:
        p.add_tools(hover)

    if 'geometry' not in df.columns:
        df_plot = df[['latitude','longitude','heading','callsign']].copy()
        df_plot['longitude'], df_plot['latitude'] = _merc(df_plot['latitude'].values, df_plot['longitude'].values)
    elif 'geometry' in df.columns:
        df_plot = df['heading','callsign'].copy()
        df_plot['longitude'] = df.geometry.x
        df_plot['latitude'] = df.geometry.y

    points = p.triangle(x='longitude', y='latitude', angle='heading', angle_units='deg', source=df_plot) 

    callsigns = df_plot['callsign'].unique()
    points.glyph.fill_color = bk.transform.factor_cmap('callsign', palette=bk.palettes.Category10[10], factors=callsigns)
    points.glyph.line_color = bk.transform.factor_cmap('callsign', palette=bk.palettes.Category10[10], factors=callsigns)

    bkplot.show(p)

def _merc(lats,lons):
    coords_xy = ([],[])
    for i in range(len(lats)):
        r_major = 6378137.0
        x = r_major * math.radians(lons[i])
        scale = x/lons[i]
        y = 180./math.pi * math.log(math.tan(math.pi/4 + lats[i] * (math.pi/180)/2)) * scale
        coords_xy[0].append(x)
        coords_xy[1].append(y)
    return coords_xy

def get_tile_providers():
    """Retrieve list of "tile providers" for use in trajectory plots
    
    Returns
    -------
    Enumeration
    """
    return Vendors
