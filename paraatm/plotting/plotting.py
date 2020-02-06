import numpy as np

import bokeh as bk
import bokeh.plotting as bkplot
from bokeh.tile_providers import Vendors, get_provider

from paraatm.Application.plotting_tools import merc


def plot_trajectory(df_in, output_file=None, output_notebook=False):
    """Plot scenario trajectory to static html and open browser
    
    Parameters
    ----------
    df_in : DataFrame
        DataFrame containing a scenario with 'latitude', 'longitude',
        'heading', and 'callsign' columns
    output_file : str
        Output file for html (if None, use bokeh default)
    output_notebook : bool
        If True, output to jupyter notebook
    """
    if output_file is not None:
        bkplot.output_file(output_file)
    elif output_notebook:
        bkplot.output_notebook()

    p = bkplot.figure(x_axis_type='mercator', y_axis_type='mercator')
    tile_provider = get_provider(Vendors.CARTODBPOSITRON)
    p.add_tile(tile_provider)

    df = df_in[['latitude','longitude','heading','callsign']].copy()
    df['longitude'], df['latitude'] = merc(df['latitude'].values, df['longitude'].values)

    points = p.triangle(x='longitude', y='latitude', angle='heading', angle_units='deg', alpha=0.5, source=df)

    callsigns = df['callsign'].unique()
    points.glyph.fill_color = bk.transform.factor_cmap('callsign', palette=bk.palettes.Category10[10], factors=callsigns)
    points.glyph.line_color = bk.transform.factor_cmap('callsign', palette=bk.palettes.Category10[10], factors=callsigns)

    bkplot.show(p)
