# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-18 23:29:41
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-20 00:23:32

from math import pi
from collections import defaultdict

import pandas as pd

from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, Button
from bokeh.models import Select, Slider, RadioButtonGroup, Div
from bokeh.palettes import Category10_10
from bokeh.layouts import row, column, Spacer
from bokeh.transform import cumsum
from bokeh.models.ranges import DataRange1d

from fetch_data import CoronaData, UpdateError

class ControlData(CoronaData) :

    def __init__(self, head=0) :
        super().__init__(head)
        self.signals_funs = {}

    def emit_signal(self, signal, * args, ** kwargs) :
        for fun in self.signals_funs.get(signal, []) :
            fun(* args, ** kwargs)

    def add_fun_signal(self, signal, fun) :
        self.signals_funs.setdefault(signal, []).append(fun)

    def get_data_country(self, country, columns) :
        if country != "World" :
            sdf = self.cdf[self.cdf["UCountry"] == country]
        else :
            sdf = self.cdf

        sdf = sdf.groupby("date")[columns].sum().reset_index()
        sdf["date"] = pd.to_datetime(sdf["date"], format="%Y/%m/%d")
        return sdf.sort_values("date")

    def get_data_date(self, date) :
        return self.cdf[self.cdf["DaysInf"] == date]

# ------------------------------------------------------------------------------------------------------------------------

class CountryInfoSource() :

    _columns_kind = {
        "New daily cases" : ["CODay", "DEDay", "REDay"],
        "All time" : ["Active", "Deaths", "Recovered"]
    }

    def __init__(self, cdata, figure, country, kind, * args, ** kwargs) :
        self.cdata = cdata
        self.figure = figure
        self.source = ColumnDataSource(* args, ** kwargs)

        self.country = country
        self.kind = kind

    @property
    def columns(self):
        return CountryInfoSource._columns_kind[self.kind]
    
    def make_source(self) :    
        df = self.cdata.get_data_country(self.country, self.columns)
        
        renamed = {"CODay" : "Daily cases", "DEDay" : "Daily deaths", 
                   "REDay" : "Daily recovered", "Active" : "Cases"}
        
        df.columns = [renamed.get(column, column) for column in df.columns]
        return df

    def change_country(self, country) :
        self.country = country
        self.make_source()

    def change_kind(self, kind) :
        self.kind = kind
        self.make_source()

    def reset(self, kind, country) :
        self.kind = kind
        self.country = country
        self.make_source()

class CountryInfoSourceLP(CountryInfoSource) :

    def __init__(self, * args, ** kwargs) :
        super().__init__(* args, ** kwargs)

    def make_source(self) :
        df = super().make_source()
        columns = df.columns[1:]

        data = defaultdict(list)
        colors = iter(Category10_10)

        for column in columns :
            data["names"].append(column)
            data["xs"].append(list(df["date"]))
            data["ys"].append(list(df[column]))
            data["colors"].append(next(colors))

        self.source.data = data
        self.figure.legend.location = "top_left"

class CountryInfoSourceStack(CountryInfoSource) :

    def __init__(self, * args, ** kwargs) :
        super().__init__(* args, ** kwargs)

    def make_source(self) :
        df = super().make_source()
        columns = df.columns[1:]
        ucol = ["x", "y", "z"]

        data = defaultdict(list)
        data["dates"] = list(df["date"])

        for idx, column in enumerate(columns) :
            data[ucol[idx]] = df[column] / df[columns].sum(axis=1)
            data["rvalues"] = df[column]

        self.source.data = data

def country_info_reset(cis_lp, cis_sp) :
    cis_lp.make_source()
    cis_sp.make_source()

def make_countries_info(cdata) :
    country = "World"
    kind = "New daily cases"
    date = cdata.cdf["date"].max()

    # linesplot
    hover = HoverTool(tooltips=[('Date', '$data_x{%F}'), ('Value', '$data_y{0,0}')], formatters={'$data_x': 'datetime'})
    lineplot = figure(plot_height=600, plot_width=600, x_axis_type='datetime', tools=[hover])
    cis_lp = CountryInfoSourceLP(cdata, lineplot, country, kind, dict(xs=[], ys=[], colors=[], names=[]))
    lineplot.multi_line('xs' ,'ys', source=cis_lp.source, line_color='colors', legend_field='names')
    
    cdata.add_fun_signal("change_country", lambda country : cis_lp.change_country(country))
    cdata.add_fun_signal("change_kind", lambda kind : cis_lp.change_kind(kind))

    # stackplot // hover not implemented for varea ?
    stackplot = figure(plot_height=200, plot_width=600, x_axis_type='datetime')
    cis_sp = CountryInfoSourceStack(cdata, stackplot, country, kind, dict(dates=[], x=[], y=[], z=[], rvalues=[], colors=[]))
    stackplot.varea_stack(stackers=["x", "y", "z"], x='dates', fill_color=Category10_10[:3], source=cis_sp.source)

    cdata.add_fun_signal("change_country", lambda country : cis_sp.change_country(country))
    cdata.add_fun_signal("change_kind", lambda kind : cis_sp.change_kind(kind))

    # Select country
    countries = cdata.countries
    countries.insert(0, "World")
    select_country = Select(title="Country", options=countries, value=country, width=150)
    select_country.on_change('value', lambda attr, old, new : cdata.emit_signal("change_country", new))

    # Select kind
    options = ["All time", "New daily cases"]
    select_kind = Select(title="Time", options=options, value=kind, width=150)
    select_kind.on_change('value', lambda attr, old, new : cdata.emit_signal("change_kind", new))

    layout = column(row(select_country, select_kind), lineplot, stackplot)

    cdata.add_fun_signal("country_info_reset", lambda : country_info_reset(cis_lp, cis_sp))
    cdata.add_fun_signal("update", lambda : country_info_reset(cis_lp, cis_sp))

    cdata.emit_signal("country_info_reset")
    
    return layout

# ------------------------------------------------------------------------------------------------------------------------

class ScatterSource() :

    def __init__(self, cdata, date, c1, c2) :
        # Specific scatter source which plot both current value and old value

        self.cursource = ColumnDataSource(dict(xs=[], ys=[], ratio=[], names=[], kind=[]))
        self.oldsource = ColumnDataSource(dict(xs=[], ys=[], ratio=[], names=[], kind=[]))
        self.linsource = ColumnDataSource(dict(xs=[], ys=[], colors=[]))

        self.cdata = cdata
        self.date = date
        self.c1 = c1
        self.c2 = c2

    def get_circle_data(self, date, kind) :
        data = self.cdata.get_data_date(date)
        return  {
            "names" : data["UCountry"],
            "xs" : data[self.c1],
            "ys" : data[self.c2],
            "ratio" : data[self.c1] / data[self.c2],
            "kind" : [kind] * len(data)
        }

    def get_line_data(self, date) :
        cols = ["UCountry", self.c1, self.c2]
        cdata = self.cdata.get_data_date(date)[cols]
        pdata = self.cdata.get_data_date(date - 1)[cols]

        df = cdata.merge(pdata, how="inner", on="UCountry")
        xvalues = zip(df[self.c1 + "_x"], df[self.c1 + "_y"])
        yvalues = zip(df[self.c2 + "_x"], df[self.c2 + "_y"])

        return {
            "xs" : list(xvalues),
            "ys" : list(yvalues),
            "colors" : ["black"] * len(df)
        }

    def make_source(self) :
        self.linsource.data = self.get_line_data(self.date)
        self.cursource.data = self.get_circle_data(self.date, "Current")
        self.oldsource.data = self.get_circle_data(self.date - 1, "Day before")
        
def scatter_change_date(scattersource, date) :
    scattersource.date = date
    scattersource.make_source()

def scatter_change_axis(scattersource, cname, xaxis) :
    if xaxis : 
        scattersource.c1 = cname
    else : 
        scattersource.c2 = cname
    
    scattersource.make_source()

def scatter_change_axis_behaviour(scatterplot, behaviour) :
    behaviour = ["Independant axis", "Shared axis"][behaviour]
    if behaviour == "Shared axis" : scatterplot.share_axis()
    elif behaviour == "Independant axis" : scatterplot.split_axis()
    else : raise ValueError("Unknown behavior")

def scatter_update(slider, cdata) :
    slider.end = cdata.cdf["DaysInf"].max()

def make_scatter(cdata) :
    col1, col2 = "Active", "Deaths"
    lastday = cdata.cdf["DaysInf"].max()

    # scatterplot
    scsource = ScatterSource(cdata, lastday, col1, col2)    
    scatterplot = figure(plot_height=750, plot_width=750)
    scatterplot.multi_line('xs' ,'ys', line_color="colors", source=scsource.linsource)
    sc1 = scatterplot.scatter('xs' ,'ys', marker="circle", size=15, line_color="navy", fill_color="#3A5785", source=scsource.cursource)
    sc2 = scatterplot.scatter('xs' ,'ys', marker="circle", size=15, line_color="navy", fill_color="#85423a", source=scsource.oldsource)

    hover = HoverTool(tooltips=[('Country', '@names'), ('XValue', '@xs{0,0}'), ('YValue', '@ys{0,0}'), ('Kind', '@kind'), ("Ratio", '@ratio')], 
        renderers=[sc1, sc2])
    scatterplot.add_tools(hover)

    # Slider
    slider = Slider(title='Days since first report', start=1, end=lastday, step=1, value=lastday)  
    slider.on_change('value', lambda attr, old, new : scatter_change_date(scsource, new))

    # Selects
    columns = list(cdata.cdf.columns[3:])

    sn1 = Select(title="X axis", options=columns, value=col1, width=150)
    sn1.on_change('value', lambda attr, old, new : scatter_change_axis(scsource, new, True))
    
    sn2 = Select(title="Y axis", options=columns, value=col2, width=150)
    sn2.on_change('value', lambda attr, old, new : scatter_change_axis(scsource, new, False))

    layout = column(row(sn1, sn2), slider, scatterplot)

    scsource.make_source()

    fun = lambda : scatter_update(slider, cdata)
    cdata.add_fun_signal("update", fun)

    return layout

# ------------------------------------------------------------------------------------------------------------------------

def update(button, cdata) :
    if button.label == "Updating ..." : return
    button.label = "Updating ..."
    result = cdata.launch_update()
    button.label = result

def launch_server(head=0) :
    cdata = ControlData(head=head)

    countries_info = make_countries_info(cdata)
    scatter_plot = make_scatter(cdata)

    button = Button(label="Update data", button_type="warning", width=150)
    button.on_click(lambda : update(button, cdata))

    text = Div(text="""
        <p><a href=https://github.com/CSSEGISandData/COVID-19 target=_blank>Data source</a>. Current data shown on this map might be not updated.
        <a href=https://github.com/jsgounot/CoronaTools target=_blank>Source code on github</a>.</p>
        <p>See also : <a href=./coronamap target=_blanck>CoronaMap - WorldWide distribution of the virus</a></p>
        """)

    layout = column(row(column(countries_info), Spacer(width=50), 
        scatter_plot, Spacer(width=50), button), text)

    curdoc().add_root(layout)
    curdoc().title = "CoronaBoard"

launch_server(head=0)