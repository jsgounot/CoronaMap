# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-26 11:38:02
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-01 03:08:21

import logging
logger = logging.getLogger("coronatools")

from datetime import datetime
from datetime import timedelta

from bokeh.models import Button, DateSlider, Select
from bokeh.models import PanTool, WheelZoomTool, ResetTool
from bokeh.layouts import row, column, Spacer

from componments.base.wmap import COLOR_MAPPER_NAME
from componments.pgcd.wmap import WMap
import layouts.utils as lutils

def carto_shift_day(upper, carto, slider) :
    # button for one upper or lower day
    value = convert_slider_date(slider.value)

    if upper : value = value + timedelta(days=1)
    else : value = value - timedelta(days=1)

    lastday = carto.pgcd.lastday()
    firstday = carto.pgcd.firstday()

    if not firstday <= value <= lastday :
        logger.debug("Value out of bond (carto day +/- 1)")
        return

    logger.debug(f"Change to value : {value}")

    carto.day = value
    slider.value = value

def convert_slider_date(value, asdate=True) :
    # took me forever to find that ...
    value = datetime.fromtimestamp(value / 1000)
    value = value.date() if asdate else value
    return value

def construct(pgcd, controller=None) :
    df_column = "Confirmed"
    lastday = pgcd.lastday()
    firstday = pgcd.firstday()
    mapper = "Log"

    # Make carto
    title = 'Coronavirus map : Day ' + str(lastday)
    tooltips = lutils.tooltips()
    tools = [PanTool(), WheelZoomTool(), ResetTool()]
    carto = WMap(pgcd, lastday, df_column, title=title, mkind=mapper, tooltips=tooltips, aspect_ratio=2, sizing_mode="scale_both", tools=tools)

    # Make a slider object: slider  
    slider = DateSlider(title="Date", start=firstday, end=lastday, value=lastday, step=1, format="%Y-%d-%m", sizing_mode="stretch_width")
    carto.link_on_change("date", slider, postfun=convert_slider_date)

    # Make buttons
    lambda_callback_bleft = lambda : carto_shift_day(False, carto, slider)
    bleft = Button(label="Day -1", button_type="success", width=200)
    bleft.on_click(lambda_callback_bleft)

    lambda_callback_bright = lambda : carto_shift_day(True, carto, slider)
    bright = Button(label="Day +1", button_type="success", width=200)
    bright.on_click(lambda_callback_bright)

    # Select for carto 
    options = [df_column for df_column in lutils.columns_description() if df_column not in ["Date"]]
    scol = Select(title="", options=options, value=df_column, width=200)
    rdesc_column = lambda column : lutils.description(column, reverse=True)
    carto.link_on_change("field", scol, postfun=rdesc_column)

    smap = Select(title="", options=list(COLOR_MAPPER_NAME.values()), value=COLOR_MAPPER_NAME[mapper], width=200)
    rdesc_cmapper = lambda name : lutils.reverse_mapping(COLOR_MAPPER_NAME, name)
    carto.link_on_change("mkind", smap, postfun=rdesc_cmapper)

    if controller :
        fun = lambda : update(slider, carto)
        controller.add_receiver("update", fun)
        new_signal = lambda country : controller.emit_signal("select_country", country)
        carto.add_receiver("doubletap", new_signal)
    
    return column(
        carto.figure, slider, 
        row(bleft, bright, scol, smap, sizing_mode="stretch_width"), 
        sizing_mode="stretch_both")