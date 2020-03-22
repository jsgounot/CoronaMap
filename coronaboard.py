# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-18 23:29:41
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-22 11:48:18

import math
from collections import defaultdict

import pandas as pd

from bokeh.core.properties import field
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import Legend, LegendItem
from bokeh.models import HoverTool, ColumnDataSource, Button
from bokeh.models import Select, Slider, RadioButtonGroup, Div
from bokeh.palettes import Category10_10
from bokeh.layouts import row, column, Spacer
from bokeh.transform import cumsum
from bokeh.models.ranges import DataRange1d
from bokeh.models.callbacks import CustomJS

from fetch_data import CoronaData, UpdateError

COLORS = Category10_10

class ControlData(CoronaData) :

    lkinds = ["Continent", "Country"]

    def __init__(self, lkind, head=0) :
        super().__init__(head)
        self.signals_funs = {}
        self.lkind = lkind

    def emit_signal(self, signal, * args, ** kwargs) :
        for fun in self.signals_funs.get(signal, []) :
            fun(* args, ** kwargs)

    def add_fun_signal(self, signal, fun) :
        self.signals_funs.setdefault(signal, []).append(fun)

    def change_lkind(self, new_idx) :
        self.lkind = ControlData.lkinds[new_idx]
        self.emit_signal("CountryMode", self.lkind)

def change_select_country(cdata, select, lkind=None) :
    lkind = lkind or cdata.lkind
    values = cdata.countries() if lkind == "Country" else ["World"] + cdata.continents()
    select.options = values
    select.value = "China" if lkind == "Country" else "World"
    return values[0]

# ------------------------------------------------------------------------------------------------------------------------

class CountryInfoSource() :

    columns_names = ["Last report cases", "All reports"] 

    _columns_kind = {
        "Last report cases" : ["CODay", "DEDay", "REDay"],
        "All reports" : ["Active", "Deaths", "Recovered"]
    }

    def __init__(self, cdata, figure, location, ckind, * args, ** kwargs) :
        self.cdata = cdata
        self.figure = figure
        self.source = ColumnDataSource(* args, ** kwargs)

        self.location = location
        self.ckind = ckind

    @property
    def columns(self):
        return CountryInfoSource._columns_kind[self.ckind]
    
    def data_from_location(self) :
        if self.location == "World" : return self.cdata.data_from_continent(None, False, world=True)
        elif self.cdata.lkind == "Continent" : return self.cdata.data_from_continent(self.location, fill=True)
        else : return self.cdata.data_from_country(self.location, fill=True)

    def make_source(self) :    
        df = self.data_from_location()
        columns = self.columns + ["Date"]
        df = df[columns]

        renamed = {"CODay" : "Daily cases", "DEDay" : "Daily deaths", 
                   "REDay" : "Daily recovered", "Active" : "Cases"}
        
        df.columns = [renamed.get(column, column) for column in df.columns]

        return df

    def change_location(self, location) :
        self.location = location
        self.make_source()

    def change_ckind(self, ckind) :
        self.ckind = ckind
        self.make_source()

    def reset(self, lkind, location, ckind) :
        self.cdata.lkind = lkind
        self.location = location
        self.ckind = ckind
        self.make_source()

class CountryInfoSourceLP(CountryInfoSource) :

    def __init__(self, * args, ** kwargs) :
        super().__init__(* args, ** kwargs)

    def make_source(self) :
        df = super().make_source()
        columns = df.columns[:3]

        data = defaultdict(list)
        colors = iter(COLORS)

        for column in columns :
            data["names"].append(column)
            data["xs"].append(list(df["Date"]))
            data["ys"].append(list(df[column]))
            data["colors"].append(next(colors))

        self.source.data = data
        self.figure.legend.location = "top_left"

class CountryInfoSourceStack(CountryInfoSource) :

    def __init__(self, * args, ** kwargs) :
        super().__init__(* args, ** kwargs)

    def make_source(self) :
        df = super().make_source()

        columns = df.columns[:3]
        ucol = ["x", "y", "z"]

        data = defaultdict(list)
        data["dates"] = list(df["Date"])

        for idx, column in enumerate(columns) :
            data[ucol[idx]] = df[column] / df[columns].sum(axis=1)
            data["rvalues"] = df[column]

        self.source.data = data

def country_info_reset(cis_lp, cis_sp) :
    cis_lp.make_source()
    cis_sp.make_source()

def make_countries_info(cdata) :
    location = "World"
    ckind = "All reports"
    date = cdata.lastday()

    # linesplot
    hover = HoverTool(tooltips=[('Date', '$data_x{%F}'), ('Value', '$data_y{0,0}')], formatters={'$data_x': 'datetime'})
    lineplot = figure(x_axis_type='datetime', tools=[hover], sizing_mode="stretch_both", min_width=10, min_height=10)
    cis_lp = CountryInfoSourceLP(cdata, lineplot, location, ckind, dict(xs=[], ys=[], colors=[], names=[]))
    lineplot.multi_line('xs' ,'ys', source=cis_lp.source, line_color='colors', legend_field='names')
    
    cdata.add_fun_signal("cinfo_change_location", lambda location : cis_lp.change_location(location))
    cdata.add_fun_signal("cinfo_change_ckind", lambda ckind : cis_lp.change_ckind(ckind))

    # stackplot // hover not implemented for varea ?
    stackplot = figure(x_axis_type='datetime', sizing_mode="stretch_width", plot_height=150, plot_width=150)
    cis_sp = CountryInfoSourceStack(cdata, stackplot, location, ckind, dict(dates=[], x=[], y=[], z=[], rvalues=[], colors=[]))
    stackplot.varea_stack(stackers=["x", "y", "z"], x='dates', fill_color=COLORS[:3], source=cis_sp.source)

    cdata.add_fun_signal("cinfo_change_location", lambda location : cis_sp.change_location(location))
    cdata.add_fun_signal("cinfo_change_ckind", lambda ckind : cis_sp.change_ckind(ckind))

    # Select country
    select_location = Select(title="Location", options=["Error"], value="Error")
    select_location.on_change('value', lambda attr, old, new : cdata.emit_signal("cinfo_change_location", new))

    # Select kind
    select_time = Select(title="Cases type", options=CountryInfoSource.columns_names, value=ckind)
    select_time.on_change('value', lambda attr, old, new : cdata.emit_signal("cinfo_change_ckind", new))

    cText = Div(text="<b>Daily evolution since first report</b>", sizing_mode="stretch_width")

    layout = column(
        cText,
        row(select_location, select_time, sizing_mode="stretch_width"),
        lineplot, 
        stackplot, 
        sizing_mode="stretch_both")

    cdata.add_fun_signal("CountryMode", lambda lkind : change_select_country(cdata, select_location, lkind))
    cdata.add_fun_signal("update", lambda : country_info_reset(cis_lp, cis_sp))
    
    return layout

# ------------------------------------------------------------------------------------------------------------------------

class DynamicBarPlot() :

    def __init__(self, cdata, name, ndisplay, * args, width=.8, ** kwargs) :
        self.cdata = cdata

        hover = HoverTool(tooltips=[('Location', '@name'), ('Value', '@top')])
        kwargs.setdefault("tools", []).append(hover)

        self.source = ColumnDataSource(data=dict(bottom=[], top=[], left=[], right=[], name=[]))
        self.figure = figure(* args, ** kwargs)
        self.figure.quad(bottom="bottom", top="top", left="left", right="right",
                         source=self.source, color="#3A5785")

        self.figure.xaxis.visible = False

        if width > 1 : raise ValueError("width must be <= 1")

        self.name = name
        self.ndisplay = ndisplay
        self.width = width
        self.data = None

    def make_source(self) :
        if self.data is None : return
        data = self.data.head(self.ndisplay)
        self.source.data = data

    def make_data(self, lkind=None) :
        lkind = lkind or self.cdata.lkind
        lastday = self.cdata.lastday(report=True)
        continent = lkind == "Continent"
        
        self.data = self.cdata.data_from_day(lastday, report=True, continent=continent, fill=True)
        self.data = self.data[[lkind, self.name]].sort_values(self.name, ascending=False)
        self.data.columns = ["name", "top"]
        self.data["bottom"] = 0

        self.data["left"] = self.data["right"] = list(range(len(self.data)))
        self.data["left"] = self.data["left"] - self.width / 2
        self.data["right"] = self.data["right"] + self.width / 2

        self.make_source()

def change_barplot_value(nname, bps) : 
    bps.name = nname
    bps.make_data()

def change_barplot_elements(nelements, bps) :
    bps.ndisplay = nelements
    bps.make_source()

def change_barplot_lkind(cdata, bps, slider, lkind) :
    elements = cdata.continents() if lkind == "Continent" else cdata.countries()

    slider.end = len(elements)
    slider.value = 5
    bps.make_data()

def make_barplot(cdata) :
    barplot = DynamicBarPlot(cdata, "Confirmed", 5, plot_height=300, plot_width=550, sizing_mode="stretch_both")

    # Select
    columns = [cdata.description(column) for column in CoronaData.data_columns]

    select_value = Select(title="Shown value", options=columns, value="Confirmed", width=220)
    select_value.on_change("value", lambda attr, old, new : change_barplot_value(cdata.description(new, reverse=True), barplot))

    slider_count = Slider(title='Number of elements', start=2, end=10, step=1, value=2, sizing_mode="stretch_width")  
    slider_count.on_change('value', lambda attr, old, new : change_barplot_elements(new, barplot))    

    cdata.add_fun_signal("CountryMode", lambda lkind : change_barplot_lkind(cdata, barplot, slider_count, lkind))
    cdata.add_fun_signal("update", lambda : barplot.make_data())

    return column(
        row(select_value, slider_count, sizing_mode="stretch_width"), 
        barplot.figure, 
        sizing_mode="stretch_both")

# ------------------------------------------------------------------------------------------------------------------------

class PieChart() :

    renamed = {"CODay" : "Confirmed", "DEDay" : "Deaths", "REDay" : "Recovered"}

    def __init__(self, cdata, columns, * args, ** kwargs) :
        self.cdata = cdata
        self.columns = columns

        hover = HoverTool(tooltips=[('Kind', '@kind'), ('Value', '@value{0,0}'), ('Percentage', '@prc{0.00%}')])
        kwargs.setdefault("tools", []).append(hover)

        self.source = ColumnDataSource(dict(angle=[], color=[], kind=[], value=[], prc=[]))
        self.figure = figure(* args, ** kwargs)
        self.figure.wedge(x=1, y=1, radius=0.8, start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                          line_color="white", fill_color='color', source=self.source)

        legend = self.make_legend()
        self.figure.add_layout(legend, 'below')
        self.figure.xaxis.visible = False
        self.figure.yaxis.visible = False

    def make_legend(self) :
        legend = []
        columns = [PieChart.renamed.get(column, column) for column in self.columns]

        for idx, column in enumerate(sorted(columns)) :
            color = COLORS[idx]
            glyph = self.figure.square([1], [1], size=2, color=color, muted_color=color)
            legend.append(LegendItem(label=column, renderers=[glyph]))

        legend = Legend(items=legend, orientation="horizontal", location="center")
        return legend

    def make_source(self, location, lkind=None) :
        lastday = self.cdata.lastday(report=True)
        df = self.cdata.data_from_day(lastday, report=True)

        lkind = lkind or self.cdata.lkind
        if lkind == "Continent" and location == "World" :
            return self.source_from_df(df)

        df = df[df[lkind] == location]
        self.source_from_df(df)

    def source_from_df(self, df) :
        df = df[self.columns]
        df.columns = [PieChart.renamed.get(column, column) for column in df.columns]

        df = df.sum().T.reset_index(name='value').rename(columns={'index':'kind'})
        df['prc'] = df['value'] / df['value'].sum()
        df['angle'] = df['prc'] * 2 * math.pi

        
        # Be sure to sort index since legend is based on sorted columns
        df = df.sort_index()
        df['color'] = COLORS[:len(self.columns)]

        self.source.data = df

def piechart_change_location(cdata, location, pie_all, pie_daily) :
    pie_all.make_source(location)
    pie_daily.make_source(location)

def piechart_update(select, pie_all, pie_daily) :
    location = select.value
    pie_all.make_source(location)
    pie_daily.make_source(location)

def make_piecharts(cdata) :
    pie_all = PieChart(cdata, ["Active", "Deaths", "Recovered"], plot_height=325, plot_width=275, x_axis_type='datetime', title="Overall", sizing_mode="scale_both")
    
    pie_daily = PieChart(cdata, ["CODay", "DEDay", "REDay"], plot_height=325, plot_width=275, x_axis_type='datetime', title="Last report", sizing_mode="scale_both")

    select_location = Select(title="Location", options=["Error"], value="Error", width=150, sizing_mode="stretch_width")
    select_location.on_change("value", lambda attr, old, new : piechart_change_location(cdata, new, pie_all, pie_daily))

    cdata.add_fun_signal("CountryMode", lambda lkind : change_select_country(cdata, select_location, lkind))
    cdata.add_fun_signal("update", lambda : piechart_update(select_location, pie_all, pie_daily))

    return column(
        select_location, 
        row(pie_daily.figure, pie_all.figure, sizing_mode="stretch_both"), 
        sizing_mode="stretch_both")

# ------------------------------------------------------------------------------------------------------------------------

def update_ctext(cdata, ctext) :
    lastday = str(cdata.lastday())[:10]
    ctext.text = "<b>Metrics from the last report (%s)</b>" %(lastday)

def make_daily_reports(cdata) :

    barplot = make_barplot(cdata)
    piecharts = make_piecharts(cdata)

    lastday = str(cdata.lastday())[:10]
    cText = Div(text="<b>Metrics from the last report (%s)</b>" %(lastday), sizing_mode="stretch_width")
    cdata.add_fun_signal("update", lambda : update_ctext(cdata, cText))

    layout = column(cText, barplot, piecharts, 
        sizing_mode="stretch_both")

    return layout

# ------------------------------------------------------------------------------------------------------------------------

class ScatterSource() :

    def __init__(self, cdata, lkind, date, c1, c2) :
        # Specific scatter source which plot both current value and old value

        self.cursource = ColumnDataSource(dict(xs=[], ys=[], ratio=[], names=[], kind=[]))
        self.oldsource = ColumnDataSource(dict(xs=[], ys=[], ratio=[], names=[], kind=[]))
        self.linsource = ColumnDataSource(dict(xs=[], ys=[], colors=[]))

        self.cdata = cdata
        self.lkind = lkind
        self.date = date
        
        self.c1 = c1
        self.c2 = c2

    def get_circle_data(self, date, kind) :
        continent = True if self.lkind == "Continent" else False
        data = self.cdata.data_from_day(date, report=True, continent=continent)

        return  {
            "names" : data[self.lkind],
            "xs" : data[self.c1],
            "ys" : data[self.c2],
            "ratio" : data[self.c1] / data[self.c2],
            "kind" : [kind] * len(data)
        }

    def get_line_data(self, date) :
        cols = [self.lkind, self.c1, self.c2]
        continent = True if self.lkind == "Continent" else False

        cdata = self.cdata.data_from_day(date, report=True, continent=continent)[cols]
        pdata = self.cdata.data_from_day(date - 1, report=True, continent=continent)[cols]

        df = cdata.merge(pdata, how="inner", on=self.lkind)
        xvalues = zip(df[self.c1 + "_x"], df[self.c1 + "_y"])
        yvalues = zip(df[self.c2 + "_x"], df[self.c2 + "_y"])

        return {
            "xs" : list(xvalues),
            "ys" : list(yvalues),
            "colors" : ["black"] * len(df)
        }

    def change_lkind(self, lkind) :
        self.lkind = lkind
        self.make_source()

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
    slider.end = cdata.lastday(report=True)

def make_scatter(cdata) :
    col1, col2 = "Active", "Deaths"
    lastday = cdata.lastday(report=True)

    # scatterplot
    scsource = ScatterSource(cdata, cdata.lkind, lastday, col1, col2)    
    scatterplot = figure(plot_height=450, plot_width=450, sizing_mode="stretch_both")
    scatterplot.multi_line('xs' ,'ys', line_color="colors", source=scsource.linsource)
    sc1 = scatterplot.scatter('xs' ,'ys', marker="circle", size=15, line_color="navy", fill_color="#3A5785", source=scsource.cursource)
    sc2 = scatterplot.scatter('xs' ,'ys', marker="circle", size=15, line_color="navy", fill_color="#85423a", source=scsource.oldsource)

    hover = HoverTool(tooltips=[('Country', '@names'), ('XValue', '@xs{0,0}'), ('YValue', '@ys{0,0}'), ('Kind', '@kind'), ("Ratio", '@ratio')], 
        renderers=[sc1, sc2])
    scatterplot.add_tools(hover)

    # Slider
    slider = Slider(title='Days since first report', start=1, end=lastday, step=1, value=lastday, sizing_mode="stretch_width")  
    slider.on_change('value', lambda attr, old, new : scatter_change_date(scsource, new))

    # Selects
    columns = [cdata.description(column) for column in CoronaData.data_columns]

    sn1 = Select(title="X axis", options=columns, value=col1, width=200)
    sn1.on_change('value', lambda attr, old, new : scatter_change_axis(scsource, cdata.description(new, reverse=True), True))
    
    sn2 = Select(title="Y axis", options=columns, value=col2, width=200)
    sn2.on_change('value', lambda attr, old, new : scatter_change_axis(scsource, cdata.description(new, reverse=True), False))

    cText = Div(text="<b>Comparison between day and day before</b>", sizing_mode="stretch_width")

    layout = column(
        cText,
        row(sn1, sn2, sizing_mode="stretch_width"), 
        slider, scatterplot, 
        sizing_mode="stretch_both")

    scsource.make_source()

    fun = lambda : scatter_update(slider, cdata)
    cdata.add_fun_signal("update", fun)
    cdata.add_fun_signal("CountryMode", lambda lkind : scsource.change_lkind(lkind))

    return layout

# ------------------------------------------------------------------------------------------------------------------------

def update(button, cdata) :
    if button.label == "Updating ..." : return
    button.label = "Updating ..."
    result = cdata.launch_update()
    button.label = result

def launch_server(head=0) :
    cdata = ControlData(head=head, lkind="Continent")

    # Toggle country / continent
    labels = ControlData.lkinds
    idx = labels.index(cdata.lkind)
    rbg = RadioButtonGroup(labels=labels, active=idx, width=150)
    rbg.on_change("active", lambda attr, old, new : cdata.change_lkind(new))

    daily_reports = make_daily_reports(cdata)
    countries_info = make_countries_info(cdata)
    scatter_plot = make_scatter(cdata)

    update_button = Button(label="Update data", button_type="warning", width=250)
    update_button.on_click(lambda : update(update_button, cdata))

    source_code_button = Button(label="Source code", button_type="success", width=150)
    source_code_button.js_on_click(CustomJS(code='window.open("https://github.com/jsgounot/CoronaTools");'))

    coronamap_button = Button(label="Corona map", button_type="primary", width=150)
    coronamap_button.js_on_click(CustomJS(code='window.open("coronamap");'))

    data_source = Button(label="Data source", button_type="success", width=150)
    data_source.js_on_click(CustomJS(code='window.open("https://github.com/CSSEGISandData/COVID-19");'))

    layout = column(
        row(
            row(rbg, update_button, coronamap_button, source_code_button, data_source), 
            sizing_mode="stretch_width"), 
        row(
            daily_reports, 
            Spacer(width=10, sizing_mode="stretch_height"), 
            countries_info, 
            #Spacer(width=10, sizing_mode="stretch_height"), 
            scatter_plot, 
            sizing_mode="stretch_both"), 
        sizing_mode="stretch_both")

    # Emit first signal to run basic plot
    cdata.emit_signal("CountryMode", cdata.lkind)

    curdoc().add_root(layout)
    curdoc().title = "CoronaBoard"

launch_server(head=0)