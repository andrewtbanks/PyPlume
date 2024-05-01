.. pyplume documentation master file, created by
   sphinx-quickstart on Tue Apr 23 19:41:32 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: ./_static/header.png 

--------------------------

Welcome to PyPlume Documentation
#################

A library for reading and analyzing ADCP and CTD data. 



**Requirements**
**********
- Windows Operating System (Linux untested)
- Python 3.11 or newer

**Installation**
**********


.. code-block:: python 

    $ pip install pyplume_install


**Getting Started**
**********

.. code-block:: python

    # read in ADCP data
    fpath_pd0 = r'.\example_data\mobile_adcp\mobile_adcp.000'
    adcp = pp.pd0.DataSet(fpath_pd0)
    
    # plot the raw echo data
    adcp.plot.four_beam_flood_plot()
    
.. image:: ./_static/mobile_adcp_flood_plot.png
    :width: 400pt

    




.. toctree::
   :maxdepth: 1
   
   API
   pd0 Dataset
   ctd Dataset
   Pose
   Data Manager
   
* :ref:`genindex`
* :ref:`modindex`

