# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-31 19:07:54
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-17 14:27:26

import os
rpath = os.path.realpath(__file__)
dname = os.path.dirname

import sys
sys.path.insert(0, dname(dname(rpath)))
print (dname(dname(rpath)))

from bokeh.io import curdoc
from pycoronadata import PersistantGeoCoronaData
from layouts import barplot as barplot_layout

from server import utils as sutils
sutils.debug_mode()

def launch_server(head=0) :
    logger = sutils.coronatool_logger()
    logger.debug("Load PGC data")

    fname = os.path.join(dname(rpath), "data.csv")
    pgcd = PersistantGeoCoronaData(fname=fname, head=head)
    logger.debug("Done loading PGC data")

    mlayout = barplot_layout.construct(pgcd, None)
    
    curdoc().add_root(mlayout)
    curdoc().title = "BarPlot"
    
    logger.debug("Finish server side")

launch_server(head=0)