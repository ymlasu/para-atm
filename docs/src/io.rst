Input and Output
================

.. py:module:: paraatm.io

Reading data
------------

The :py:mod:`paraatm.io` module provides functions for reading from common data formats.  Currently, this includes the Integrated Flight Format (IFF) and NATS simulation output files.

.. autofunction:: paraatm.io.iff.read_iff_file
.. autofunction:: paraatm.io.nats.read_nats_output_file

Utilities
---------

.. py:module:: paraatm.io.utils
               
General-purpose utility functions are provided in the :py:mod:`paraatm.io.utils` module.  :py:func:`~paraatm.io.utils.read_data_file` will try and automatically detect the file type.  :py:func:`~paraatm.io.utils.write_csv_file` writes a DataFrame back to a CSV format file that can be subsequently read back in.

.. autofunction:: paraatm.io.utils.read_data_file
.. autofunction:: paraatm.io.utils.write_csv_file
.. autofunction:: paraatm.io.utils.read_csv_file

Example: parse large IFF file
-----------------------------

The following example illustrates how :py:func:`~paraatm.io.iff.read_iff_file` can be used to parse select values from a very large IFF file and store the results to a new file.  This way, the extracted results can be re-used without the need to re-read the large file, which may be time consuming.

.. code-block:: python

   from paraatm import io

   # Read track point data (record 3) for callsign 'ABC123':
   df = io.iff.read_iff_file('huge_data_file.iff', record_types=3, callsigns='ABC123')
   
   # Write extracted data to new file in CSV format:
   io.utils.write_csv_file(df, 'extracted_data.csv')

   # Read extracted data back:
   io.utils.read_data_file('extracted_data.csv')
