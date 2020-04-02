Plotting
========

.. py:module:: paraatm.plotting

Trajectory data that are stored in a `DataFrame` returned by :py:func:`paraatm.io.iff.read_iff_file` or :py:func:`paraatm.io.nats.read_nats_output_file` can be plotted directly.  Plotting is handled using the `Bokeh <https://bokeh.org>`_ library, which renders interactive plots in HTML.

.. autofunction:: paraatm.plotting.plotting.plot_trajectory

The following is an example trajectory plot of the data in `sample_data/IFF_SFO_ASDEX_ABC123.csv` created using :py:func:`~paraatm.plotting.plotting.plot_trajectory`:

.. image:: /_static/bokeh_plot.png
