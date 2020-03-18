# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-16 02:56:21
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-18 03:09:54

import numpy as np
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
        self.setup(kwargs)

    def setup(self, kwargs) :
        self.data = {}
        self.xshift = {}
        self.shift_format = self.get_shift_format(kwargs.get("x_axis_type", None))   

    def __contains__(self, name) :
        return name in self.data

    @property
    def names(self):
        return sorted(self.data.keys())
    
    def get_shift_format(self, x_axis_type=None) :
        fun = lambda x : x
        if x_axis_type == "datetime" : fun = lambda x : timedelta(x)
        return fun

    def get_shift(self, name) :
        value = self.shift_format(self.xshift.get(name, 0))
        return value

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
        if name in self.xshift : self.xshift.pop(name)
        if update : self.update_data()

    def make_source(self) :
        data = {"xs" : [], "ys" : [], "colors" : [], "names" : []}
        for name in sorted(self.data) :
            data["names"].append(name)
            for key, value in self.data[name].items() :
                if key == "xs" : value = value + self.get_shift(name)
                data[key].append(value)
        return data

    def switch_data(self, name, direction, update=True) :
        assert direction in ("right", "left")
        value = 1 if direction == "right" else -1
        self.xshift[name] = self.xshift.get(name, 0) + value
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
        self.xshift = {}
        if update : self.update_data()

    def overlay_xaxis(self) :
        # search for overlay between series
        extract = lambda name, column : self.data[name][column]                 
        values = lambda name : (extract(name, 'xs'), extract(name, 'ys'))

        names = list(self.data)      
        reference = values(names[0])

        for name in names[1:] :
            query = values(name)
            diff = MultiLinesPlot.overlay_two_lines(reference, query)
            self.xshift[name] = diff

        self.update_data()    
        
    @staticmethod
    def search_overlay(a1, a2) :
        fdiff = lambda a1, a2 : np.abs(a1 - a2).sum()
        diff = fdiff(a1, a2)
        assert len(a1) == len(a2)
        a1 = a1.copy()

        for i in range(len(a1)) :
            a1[1:] = a1[:-1]
            a1[0] = 0

            ndiff = fdiff(a1, a2)
            if ndiff > diff : break
            diff = ndiff

        return i, diff

    @staticmethod
    def overlay_two_lines(reference, values) :
        a1 = np.array(reference[1])
        a2 = np.array(values[1])

        s1, d1 = MultiLinesPlot.search_overlay(a1, a2)
        s2, d2 = MultiLinesPlot.search_overlay(a2, a1)

        if d1 < d2 :
            return -s1
        else :
            return s2

class MultiLinesPlots(MultiLinesPlot) :

    def __init__(self, atypes=["linear", "log"], ** kwargs) :

        self.source = ColumnDataSource(dict(xs=[], ys=[], colors=[], names=[]))

        self.distplots = {atype : MultiLinesPlot(y_axis_type=atype, source=self.source, ** kwargs)
            for atype in atypes}

        self.panels = [Panel(child=dp.figure, title=atype)
            for atype, dp in self.distplots.items()]

        self.tabs = Tabs(tabs=self.panels)
        self.setup(kwargs)

    def __iter__(self) :
        yield from self.distplots.values()

    def update_data(self, source=None) :
        self.source.data = self.make_source()
        for distplot in self :
            distplot.figure.legend.location = "top_left"