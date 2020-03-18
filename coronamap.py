# make_data.py
# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-10 15:27:40
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-18 15:52:14

import os

from bokeh import events
from bokeh.io import show, curdoc
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource
from bokeh.models import Slider, HoverTool, Button, Div, Select, MultiSelect
from bokeh.models.mappers import LogColorMapper, LinearColorMapper
from bokeh.palettes import YlOrRd9
from bokeh.layouts import row, column, Spacer
from bokeh.events import DoubleTap
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn

from multilineplot import MultiLinesPlots
from fetch_data import CoronaData, find_count_lon_lat

class CoronaDataBokeh(CoronaData) :

    def __init__(self, head=0) :
        super().__init__(head)

        self.gdfd = self.gdf.set_index("UCountry")["geometry"].to_dict()

        self.last_day = self.get_last_day()
        self.current_day = self.last_day

        gj = self.current_jdata
        self.geosource = GeoJSONDataSource(geojson=gj)

        self.acols = {
            "date" : None, "Confirmed" : '0,0', "Deaths" : '0,0', "Recovered" : '0,0', "DRate" : '0%', 
            "CODay" : '0,0', "DEDay" : '0,0', "REDay" : '0,0', "PopSize" : '0,0', "PrcCont" : '0.000%',
            "CO10k" : '0.000', "DE10k" : '0.000', "RE10k" : '0.000'
            }

        self.carto_current_acol = "Confirmed"
        self.carto_current_mapper = "Log scale color mapping"
        self.dp_current_acol = "Confirmed"

        self.signals_funs = {}

    def hoover_format(self) :
        for acol, formating in self.acols.items() :
            if not formating : yield (self.description(acol, acol), "@" + acol)
            else : yield (self.description(acol, acol), '@%s{%s}' %(acol, formating))

    def get_last_day(self) :
        return int(self.cdf["DaysInf"].max())

    @property
    def current_jdata(self):
        return self.df2json(self.current_day)
    
    def set_day(self, day) :
        if day <= 0 or day > self.last_day :
            raise ValueError()
        self.current_day = day
        return self.current_jdata

    def increase_day(self) :
        if self.current_day == self.last_day :
            raise ValueError()
        self.current_day += 1

    def decrease_day(self) :
        if self.current_day == 0 :
            raise ValueError()
        self.current_day -= 1

    def get_max_min(self, column) :
        df = self.cdf[self.cdf[column].notna()]
        df = df.groupby(["date", "UCountry"])[column].sum().astype(int)
        return df.min(), df.max()

    def emit_signal(self, signal, ** kwargs) :
        for fun in self.signals_funs.get(signal, []) :
            fun(** kwargs)

    def add_fun_signal(self, signal, fun) :
        self.signals_funs.setdefault(signal, []).append(fun)

    def get_country(self, lon, lat) :
        return find_count_lon_lat(lon, lat, self.gdfd)

def callback_slider(value, figure, cdata) :
    figure.title.text = 'Coronavirus map : Day ' + str(value)
    cdata.geosource.geojson = cdata.set_day(value)

def callback_button(upper, figure, cdata, slider) :
    value = slider.value

    try : cdata.increase_day() if upper else cdata.decrease_day()
    except ValueError : return

    value, jdata = cdata.current_day, cdata.current_jdata

    figure.title.text = 'Coronavirus map : Day ' + str(value)
    cdata.geosource.geojson = jdata
    slider.value = value

def callback_map_dt(event, cdata) :
    lon, lat = event.x, event.y
    country = cdata.get_country(lon, lat)
    cdata.emit_signal("dp_country_change", country=country)

def change_color_map(select_col, select_mapper, patches, cdata) :
    cdata.carto_current_acol = column = select_col.value
    cdata.carto_current_mapper = mapper = select_mapper.value

    patches = patches.glyph
    low, high = cdata.get_max_min(column)
    
    if mapper == "Log scale color mapping" :
        mapper = LogColorMapper(palette=YlOrRd9[::-1], low=1, high=high)
    elif mapper == "Linear scale color mapping" :
        mapper = LinearColorMapper(palette=YlOrRd9[::-1], low=1, high=high)
    else :
        raise ValueError("Unknown mapper found : %s" %(mapper))

    patches.fill_color = {'field' : column, 'transform' : mapper}

def construct_map_layout(cdata) :
    low, high = cdata.get_max_min(cdata.carto_current_acol)
    log_mapper = LogColorMapper(palette=YlOrRd9[::-1], low=1, high=high)
    
    hover = HoverTool(tooltips=[('Country','@UCountry')] + [value for value in cdata.hoover_format()])

    carto = figure(title='Coronavirus map : Day ' + str(cdata.last_day), height=750, tools=[hover])
    
    patches = carto.patches('xs','ys', source=cdata.geosource, fill_color={'field' : cdata.carto_current_acol, 'transform' : log_mapper},
              line_color='black', line_width=0.25, fill_alpha=1)

    lambda_callback_map_dt = lambda event : callback_map_dt(event, cdata)
    carto.on_event(DoubleTap, lambda_callback_map_dt)

    # Make a slider object: slider
    slider = Slider(title='Days since first infection', start=1, end=cdata.last_day, step=1, value=cdata.last_day)  
    lambda_callback_slider = lambda attr, old, new : callback_slider(new, carto, cdata)
    slider.on_change('value', lambda_callback_slider)
    
    # Make buttons
    lambda_callback_bleft = lambda : callback_button(False, carto, cdata, slider)
    bleft = Button(label="Day -1", button_type="success", width=150)
    bleft.on_click(lambda_callback_bleft)

    lambda_callback_bright = lambda : callback_button(True, carto, cdata, slider)
    bright = Button(label="Day +1", button_type="success", width=150)
    bright.on_click(lambda_callback_bright)

    # Select for carto
    options = [value for value in cdata.acols if value not in ["date"]]
    scol = Select(title="", options=options, value=cdata.carto_current_acol, width=150)
    smap = Select(title="", options=["Log scale color mapping", "Linear scale color mapping"], 
                    value=cdata.carto_current_mapper, width=200)


    lambda_change_color_map = lambda attr, old, new : change_color_map(scol, smap, patches, cdata)
    scol.on_change('value', lambda_change_color_map)
    smap.on_change('value', lambda_change_color_map)

    text1 = Div(text="How to : Double tap on map or select using the combobox under right side graph. 10 countries max can be selected at once.")
    text2 = Div(text="<a href=https://github.com/CSSEGISandData/COVID-19 target=_blank>Data source</a>. Current data shown on this map might be not updated.")
    text3 = Div(text="<a href=https://github.com/jsgounot/CoronaMap target=_blank>Source code on github</a>.")
    
    return column(carto, slider, row(bleft, bright, scol, smap), text1, text2, text3, sizing_mode="stretch_width")

def callback_distplots_change(column, cdata, distplots) :
    cdata.dp_current_acol = column
    data = cdata.extract_data_countries(distplots.names, column)
    distplots.add_elements(data, clear=True)

def update_ms(country, ms) :
    options = ms.options
    if country in options :
        options.remove(country)
    else :
        options.append(country)
    ms.options = options

def callback_distplots_country(country, cdata, distplots, ms) :
    if not isinstance(country, str) : return

    if country in distplots :
        distplots.remove_element(country)

    else :
        xs, ys = cdata.extract_data_country(country, cdata.dp_current_acol)
        distplots.add_element(country, xs, ys)

    update_ms(country, ms)

def callback_distplots_reset(distplots, cdata) :  
    column = cdata.dp_current_acol
    # little trick with minimal overload
    callback_distplots_change(column, cdata, distplots)

def callback_distplots_clear(distplots, ms) :
    distplots.clear()
    ms.options = []

def callback_auto_overlay(distplots, cdata) :
    if len(distplots.names) < 2 : return
    distplots.overlay_xaxis()

def construct_distplot_layout(cdata) :
    distplots = MultiLinesPlots(plot_height=450, plot_width=500,x_axis_type='datetime')

    # select column
    options = list(cdata.acols)
    options.remove("PopSize")
    select_column = Select(title="", options=options, value=cdata.dp_current_acol, width=150)

    lambda_callback_dp_change = lambda attr, old, new : callback_distplots_change(new, cdata, distplots)
    select_column.on_change('value', lambda_callback_dp_change)

    # multiselect
    ms = MultiSelect(title="Selected countries", options=[], height=100)

    button_left = Button(label="Slide left", button_type="success", width=150)
    cbbl = lambda : distplots.switch_multiple_data(ms.value, "left")
    button_left.on_click(cbbl)

    button_right = Button(label="Slide right", button_type="success", width=150)
    cbbr = lambda : distplots.switch_multiple_data(ms.value, "right")
    button_right.on_click(cbbr) 

    button_auto = Button(label="Auto overlay", button_type="success", width=150)
    cbba = lambda : callback_auto_overlay(distplots, cdata)
    button_auto.on_click(cbba) 

    # select country 
    options = sorted(cdata.gdf["UCountry"].unique())
    select_country = Select(title="", options=options, value='China', width=150)    

    lambda_callback_button_country = lambda : callback_distplots_country(select_country.value, cdata, distplots, ms)
    button_country = Button(label="Add country", button_type="success", width=150)
    button_country.on_click(lambda_callback_button_country)  

    # other
    lambda_callback_dp_country = lambda country : callback_distplots_country(country, cdata, distplots, ms)
    cdata.add_fun_signal("dp_country_change", lambda_callback_dp_country)

    reset_button = Button(label="Reset overlay", button_type="warning", width=150)
    lambda_callback_rbutton = lambda : callback_distplots_reset(distplots, cdata)
    reset_button.on_click(lambda_callback_rbutton)

    clear_button = Button(label="Clear graph", button_type="warning", width=150)
    lambda_callback_cbutton = lambda : callback_distplots_clear(distplots, ms)
    clear_button.on_click(lambda_callback_cbutton)

    # info text
    text1 = Div(text="Add another country or change current metrics")
    text2 = Div(text="Manual or automatic overlay data. Manual correction : Select one or more country below and switch left/right")

    text3 = Div(text="""
        <p>DRate : Death rate = Deaths / (Deaths + Recovered)</p>
        <p>PrcCont : Percentage of the country population contaminated</p>
        <p>CO10K : Number of confirmed cases per 10,000 habitants</p>
        <p>CODay : New confirmed cases each day</p>
        """)

    return column(distplots.tabs, text1, row(select_country, button_country, select_column),
        text2, ms, row(button_auto, button_left, button_right), row(reset_button, clear_button),
        text3)

def launch_server(head=0) :
    cdata = CoronaDataBokeh(head=head)
    map_layout = construct_map_layout(cdata)
    spacer = Spacer(width=10)
    dis_layout = construct_distplot_layout(cdata)
    
    layout = row(map_layout, spacer, dis_layout)
    curdoc().add_root(layout)
    curdoc().title = "CoronaMap"

launch_server(head=0)