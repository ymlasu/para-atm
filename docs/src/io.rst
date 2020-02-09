Input and Output
================

Reading data files
------------------

.. py:module:: paraatm.io

The :py:mod:`paraatm.io` module provides functions for reading from common data formats.  Currently, this includes the Integrated Flight Format (IFF) and NATS simulation output files.

.. autofunction:: paraatm.io.iff.read_iff_file

.. autofunction:: paraatm.io.nats.read_nats_output_file

A general function is also available, which will try and automatically detect the file type, calling the appropriate function:

.. autofunction:: paraatm.io.utils.read_data_file
