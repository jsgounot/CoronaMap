# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-16 02:56:21
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-16 03:30:25

from datetime import timedelta
from bokeh.plotting import figure
from bokeh.palettes import Category10_10
from bokeh.models import HoverTool, ColumnDataSource, Panel, Tabs

class MultiLinesPlot() :

    def __init__(self, source=None, ** kwargs) :
        
        if source is None : 
            self.source = ColumnDataSource(dict(xs=[], ys=[], colors=[], names=[]))
        else :
            self.source = source

        hover = HoverTool(tooltips=[('Country','@names'), ('Date', '$data_x{%F}'), ('Value', '$data_y{0,0}')], 
            formatters={'$data_x': 'datetime'})
        
        kwargs.setdefault("tools", []).append(hover)

        self.figure = figure(** kwargs)
        self.figure.multi_line('xs' ,'ys', source=self.source, line_color='colors', legend_field='names')
        
        self.data = {}

    def __contains__(self, name) :
        return name in self.data

    @property
    def names(self):
        return sorted(self.data.keys())
    
    def get_color(self) :
        colors = {value["colors"] for value in self.data.values()}
        return next(color for color in Category10_10
            if color not in colors)

    def add_element(self, name, xs, ys, update=True) :
        if name in self : raise ValueError("Value already in data")
        try : color = self.get_color()
        except StopIteration : return
        self.data[name] = {"xs" : xs, "ys" : ys, "colors" : color}
        if update : self.update_data()

    def add_elements(self, dic, clear=False) :
        if clear : self.clear(update=False)
        for name, values in dic.items() :
            xs, ys = values["xs"], values["ys"]
            self.add_element(name, xs, ys, update=False)
        self.update_data()

    def remove_element(self, name, update=True) :
        if name not in self : raise ValueError("Value not found in data")
        self.data.pop(name)
        if update : self.update_data()

    def make_source(self) :
        data = {"xs" : [], "ys" : [], "colors" : [], "names" : []}
        for name in sorted(self.data) :
            data["names"].append(name)
            for key, value in self.data[name].items() :
                data[key].append(value)
        return data

    def switch_data(self, name, direction, update=True) :
        assert direction in ("right", "left")
        value = 1 if direction == "right" else -1
        self.data[name]["xs"] += timedelta(value)
        if update : self.update_data()

    def switch_multiple_data(self, names, direction, update=True) :
        for name in names :
            self.switch_data(name=name, direction=direction, update=False)
        if update : self.update_data()

    def update_data(self) :
        self.source.data = self.make_source()
        self.figure.legend.location = "top_left"

    def clear(self, update=True) :
        self.data = {}
        if update : self.update_data()

class MultiLinesPlots(MultiLinesPlot) :

    def __init__(self, atypes=["linear", "log"], ** kwargs) :

        self.source = ColumnDataSource(dict(xs=[], ys=[], colors=[], names=[]))

        self.distplots = {atype : MultiLinesPlot(y_axis_type=atype, source=self.source, ** kwargs)
            for atype in atypes}

        self.panels = [Panel(child=dp.figure, title=atype)
            for atype, dp in self.distplots.items()]

        self.tabs = Tabs(tabs=self.panels)
        self.data = {}

    def __iter__(self) :
        yield from self.distplots.values()

    def update_data(self) :
        self.source.data = self.make_source()
        for distplot in self :
            distplot.figure.legend.location = "top_left"