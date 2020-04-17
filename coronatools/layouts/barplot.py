# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-26 12:35:34
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-01 01:20:39

from datetime import datetime

import pandas as pd

from bokeh.models import Slider, Select
from bokeh.layouts import row, column
from bokeh.models import DateSlider

from componments.pgcd.bar import DynamicBarPlot
from layouts import utils as lutils

def set_region(pgcd, slider, region) :
    count = len(pgcd.unique(region))
    slider.end = count

def convert_slider_date(value) :
    # took me forever to find that ...
    return datetime.fromtimestamp(value / 1000).date()

def construct(pgcd, controller=None) :
    lastday = pgcd.lastday()
    firstday = pgcd.firstday()

    default_column = "Confirmed"
    default_geocolumn = "Country"

    # Figure
    barplot = DynamicBarPlot(pgcd, None, "Confirmed", lastday, ndisplay=20, aspect_ratio=4, sizing_mode="scale_width")

    # Select day
    slider_date = DateSlider(title="Date", start=firstday, end=lastday, value=lastday, step=1, format="%Y-%d-%m", sizing_mode="stretch_width")
    barplot.link_on_change("date", slider_date, postfun=convert_slider_date)

    # nice but not really effective. Keep it here if needed later somewhere else
    #slider_date = DatePicker(sizing_mode="stretch_width", min_date=firstday, max_date=lastday, value=lastday)

    # Select geocolumn (country / continent)
    select_region = Select(title="Region", options=["Continent", "Country"], value="Error", sizing_mode="stretch_width")
    barplot.link_on_change("geocolumn", select_region)

    # Select location
    columns = [df_column for df_column in lutils.columns_description() if df_column not in ("Date",)]
    select_column = Select(title="Sort by", options=columns, value="Confirmed", width=100)
    postfun = lambda column : lutils.description(column, reverse=True)
    barplot.link_on_change("column", select_column, postfun=postfun)
   
    # Slider
    slider_ndisplay = Slider(title='Number of elements', start=2, end=10, step=1, value=5, sizing_mode="stretch_width")
    barplot.link_on_change("ndisplay", slider_ndisplay)
    select_region.on_change("value", lambda attr, old, new : set_region(pgcd, slider_ndisplay, new))

    # Controller
    if controller :
        controller.add_receiver("change_region", lambda region : barplot_new_region(barplot, slider_ndisplay, region))
        barplot.link_to_controller("date", controller, "bp_date")
        barplot.add_receiver("doubletap", lambda location : controller.emit_signal("location", location))

    select_region.value = default_geocolumn

    return column(
        row(
            #select_date,
            select_region, 
            select_column,  
            sizing_mode="stretch_width"), 
        slider_ndisplay,
        slider_date,
        barplot.figure,
        sizing_mode="stretch_both")