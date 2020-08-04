Plotting
========

.. py:module:: paraatm.plotting

Trajectory data that are stored in a `DataFrame` returned by :py:func:`paraatm.io.iff.read_iff_file` or :py:func:`paraatm.io.nats.read_nats_output_file` can be plotted directly.  Plotting is handled using the `Bokeh <https://bokeh.org>`_ library, which renders interactive plots in HTML.

.. autofunction:: paraatm.plotting.plot_trajectory

The following is an example trajectory plot of the data in `sample_data/IFF_SFO_ASDEX_ABC123.csv` created using :py:func:`~paraatm.plotting.plot_trajectory`:

.. For latex-PDF output, include a PNG image, since the
   bokeh-generated plot only shows up in the HTML output

.. only:: latex

   .. image:: /_static/bokeh_plot.png

.. bokeh-plot::

   from paraatm.plotting import plot_trajectory
   from paraatm.io.iff import read_iff_file

   df = read_iff_file('../paraatm/sample_data/IFF_SFO_ASDEX_ABC123.csv')

   plot_trajectory(df, plot_width=700, plot_height=600)

.. autofunction:: paraatm.plotting.get_tile_providers
