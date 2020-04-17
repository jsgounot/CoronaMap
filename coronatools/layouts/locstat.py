# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-26 12:37:22
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-01 03:26:46

from bokeh.models import Select, DateRangeSlider
from bokeh.layouts import row, column

from componments.pgcd.mlp import MultiLinesPlotMapping
from componments.pgcd.stack import StackPlot

CASES_DESC = {
    "global" : "Cumulative cases",
    "daily" : "Daily cases"
}

CASES_COLUMNS = {
    "global" : ["Active", "Deaths", "Recovered"],
    "daily" : ["CODay", "DEDay", "REDay"]
}

def kind_from_desc(kind) :
    return {v : k for k, v in CASES_DESC.items()}[kind]

def change_region(pgcd, select, region) :
    values = pgcd.unique(region)
    select.options = values
    select.value = values[0]

def construct(pgcd, controller=None) :
    ckind = "global"
    region = "Continent"
    location = "Asia"

    # plots
    mlp = MultiLinesPlotMapping(pgcd, ckind, CASES_COLUMNS, aspect_ratio=2, sizing_mode="scale_both")
    spl = StackPlot(pgcd, ckind, CASES_COLUMNS, asprc=True, plot_height=150, sizing_mode="stretch_width", tools=[])

    # Toggle geocolumn (country / continent)
    regions, default_regions_idx = ["Country", "Continent"], 0
    select_region = Select(title="Region", options=["Continent", "Country"], value="Error", sizing_mode="stretch_both")
    mlp.link_on_change("geocolumn", select_region)
    spl.link_on_change("geocolumn", select_region)

    # Select country
    select_location = Select(title="Location", options=["Error"], value="Error", sizing_mode="stretch_both")
    mlp.link_on_change("location", select_location)
    spl.link_on_change("location", select_location)
    select_region.on_change("value", lambda attr, old, new : change_region(pgcd, select_location, new))

    # Select kind
    select_time = Select(title="Cases type", options=list(CASES_DESC.values()), value=CASES_DESC[ckind], sizing_mode="stretch_both")
    mlp.link_on_change("kind", select_time, postfun=kind_from_desc)
    spl.link_on_change("kind", select_time, postfun=kind_from_desc)

    # Slider for date range ?
    #start, end = pgcd.firstday(), pgcd.lastday()
    #slider = DateRangeSlider(start=start, end=end, value=(start, end), sizing_mode="stretch_width")

    # controller (to fill)
    if controller :
        mlp.link_to_controller("geocolumn", controller, "change_region")
        spl.link_to_controller("geocolumn", controller, "change_region")
        controller.add_receiver("change_region", lambda region : change_region(pgcd, select_location, region))

    # trigger event
    select_region.value = region
    select_location.value = location

    layout = column(
        row(select_region, select_location, select_time, sizing_mode="stretch_width"),
        mlp.figure, 
        spl.figure, 
        #slider,
        sizing_mode="stretch_both")
    
    return layout