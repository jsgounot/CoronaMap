# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-16 02:56:21
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-16 17:40:31

from datetime import timedelta

import pandas as pd
import numpy as np

from bokeh.plotting import figure
from bokeh.palettes import Category10_10 as pcolors
from bokeh.models import HoverTool, ColumnDataSource, Panel, Tabs

from componments.base.utils import BaseChart, ToolTips
from componments.base.errors import SourceException

class MultiLinesPlot(BaseChart) :

    def __init__(self, * args, tooltips=None, legend_location="top_left", scatter=True, 
                default_alpha=.8, colors={}, line_source=None, scatter_source=None,
                kwargs_hovertool={}, kwargs_scatter={}, ** kwargs) :
        
        # Do not try to replace xs and xy, otherwith data_x and data_y will not work anymore
        self._source = line_source or ColumnDataSource(dict(xs=[], ys=[], colors=[], hue=[]))

        default_tooltips = MultiLinesPlot.default_tooltips()
        tooltips = tooltips or default_tooltips

        hover = HoverTool(tooltips=tooltips.bokeh_format(), ** kwargs_hovertool)
        kwargs.setdefault("tools", []).append(hover)

        self._figure = figure(* args, ** kwargs)
        self._figure.multi_line("xs", "ys", source=self._source, line_color='colors', legend_field="hue")
        
        if scatter :
            kwargs = {"marker" : "circle", "size" : 8, "line_color" : "black"}
            kwargs.update(kwargs_scatter)
            
            self._source_scatter = scatter_source or ColumnDataSource(dict(xs=[], ys=[], fcolors=[], alpha=[]))
            self._figure.scatter("xs", "ys", source=self._source_scatter, fill_color="fcolors", 
                                 alpha="alpha", ** kwargs)
            
            self._default_alpha = default_alpha

        self._scatter = scatter
        self._legend_location = legend_location
        self._colors = colors
        self.setup(kwargs)

    def setup(self, kwargs) :
        self._df = pd.DataFrame()
        self._xshift = {}
        self._xshift_format = self.get_shift_format(kwargs.get("x_axis_type", None))
        self._yshift = {}
        self._yshift_format = self.get_shift_format(kwargs.get("y_axis_type", None))
        self._ignore = False

    @staticmethod
    def default_tooltips() :
        return ToolTips(
            {"name" : "data_x", "lead" : "$", "description" : "XValue"},
            {"name" : "data_y", "lead" : "$", "description" : "YValue"}
            )

    def get_shift_format(self, axis_type=None) :
        fun = lambda x : x
        if axis_type == "datetime" : fun = lambda x : timedelta(x)
        return fun

    # -----------------------------------------------------------------

    def __contains__(self, name) :
        return name in self.data

    @property
    def names(self):
        return sorted(self.data.keys())

    @property
    def figure(self):
        return self._figure
    
    @property
    def ignore(self) :
        return self._ignore
    
    @ignore.setter
    def ignore(self, ignore) :
        self._ignore = ignore

    @property
    def df(self):
        return self._df
    
    @df.setter
    def df(self, df) :
        if not isinstance(df, pd.DataFrame) :
            raise ValueError("df must be a pandas DataFrame")

        self._df = df
        self.set_data_source()

    @property
    def xshift(self):
        return self._xshift
    
    @property
    def yshift(self):
        return self._yshift

    @property
    def legend_location(self):
        return self._legend_location

    @property
    def default_alpha(self):
        return self._default_alpha
        self.set_data_source()

    @property
    def colors(self):
        return self._colors
    
    # -----------------------------------------------------------------
  
    def set_data_source(self, data=None, ignore=False) :
        data = data or self.make_data_source()
        if not data and self.ignore == False : raise SourceException("No data source to provide")
        
        self._source.data = data

        if self.legend_location :
            self.figure.legend.location = self.legend_location

        if self._scatter :
            data =  self.make_data_scatter_source(data)
            if not data and self.ignore == False : raise SourceException("No data source to provide")
            self._source_scatter.data = data

    def make_data_source(self, df=None) :
        # multi_line does not work if you only gave a data frame
        # you have to convert it first to dict
        if df is None : df = self.df
        self._df = df       
        
        data = {"hue" : [], "colors" : [], "xs" : [], "ys" : []}
        
        # we keep previous colors (if still used in this plot)
        # we update the color reference with color argument
        used_colors = self.get_colors()
        used_colors.update(self.colors)
        used_colors = {column : value for column, value in used_colors.items() if column in df.columns}
        colors = (color for color in pcolors if color not in set(used_colors.values()))

        for column in sorted(df.columns) :
            data["hue"].append(column)
            data["xs"].append(list(df.index))
            data["ys"].append(list(df[column]))

            color = used_colors.get(column, None)
            if color is None : color = next(colors)
            data["colors"].append(color)

        return data

    def make_data_scatter_source(self, data) :
        ndata = {"xs" : [], "ys" : [], "fcolors" : [], "alpha": []}
        if not data : return ndata

        for idx, color in enumerate(data["colors"]) :
            ndata["xs"].extend(data["xs"][idx])
            ndata["ys"].extend(data["ys"][idx])
            ndata["fcolors"].extend([color] * len(data["xs"][idx]))
            ndata["alpha"].extend([self.default_alpha] * len(data["xs"][idx]))

        return ndata

    def get_colors(self) :
        data = self._source.data
        names = data.get("hue", [])
        colors = data.get("colors", [])
        return dict(zip(names, colors))

    # -----------------------------------------------------------------

    """
    def get_shift(self, name) :
        value = self.shift_format(self.xshift.get(name, 0))
        return value

    def add_element(self, name, xs, ys, update=True) :
        if name in self : raise ValueError("Value already in data")
        try : color = self.get_color()
        except StopIteration : return
        self.data[name] = {"xs" : xs, "ys" : ys, "colors" : color}
        if update : self.set_data()

    def add_elements(self, dic, clear=False) :
        if clear : self.clear(update=False)
        for name, values in dic.items() :
            xs, ys = values["xs"], values["ys"]
            self.add_element(name, xs, ys, update=False)
        self.set_data()

    def remove_element(self, name, update=True) :
        if name not in self : raise ValueError("Value not found in data")
        self.data.pop(name)
        if name in self.xshift : self.xshift.pop(name)
        if update : self.set_data()

    def switch_data(self, name, direction, update=True) :
        assert direction in ("right", "left")
        value = 1 if direction == "right" else -1
        self.xshift[name] = self.xshift.get(name, 0) + value
        if update : self.set_data()

    def switch_multiple_data(self, names, direction, update=True) :
        for name in names :
            self.switch_data(name=name, direction=direction, update=False)
        if update : self.set_data()

    def clear(self, update=True) :
        self.data = {}
        self.xshift = {}
        if update : self.set_data()

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

        self.set_data()    
        
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

    """
