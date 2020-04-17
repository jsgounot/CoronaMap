# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-26 11:34:33
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-29 03:15:29

import math 

import pandas as pd

from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.models import Legend, LegendItem
from bokeh.transform import cumsum
from bokeh.palettes import Category10_10 as cpalette
from bokeh.events import DoubleTap

from componments.base.utils import BaseChart, ToolTips
from componments.base.errors import SourceException

class PieChart(BaseChart) :

    circle_radius = .8
    circle_x = 1
    circle_y = 1

    def __init__(self, * args, tooltips=None, colors=None, kwargs_hovertool={}, ** kwargs) :
        tooltips = tooltips or PieChart.default_tooltips()
        hover = HoverTool(tooltips=tooltips.bokeh_format(), ** kwargs_hovertool)
        kwargs.setdefault("tools", []).append(hover)

        self._source = ColumnDataSource(dict(angle=[], color=[], prc=[], name=[], value=[]))

        self.figure = figure(* args, ** kwargs)
        self.figure.wedge(x=PieChart.circle_x, y=PieChart.circle_y, radius=PieChart.circle_radius, 
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color="white", fill_color='color', source=self.source)

        self.figure.on_event(DoubleTap, self.doubletap)

        self._legend = None
        self._colors = colors or cpalette
        self._cmap =  None

    @property
    def colors(self):
        return self._colors

    @property
    def cmap(self):
        return self._cmap
    
    @property
    def legend(self):
        return self._legend
    
    @property
    def source(self):
        return self._source        

    @staticmethod
    def default_tooltips() :
        return ToolTips(
            {"name" : "name", "description" : "Metric"},
            {"name" : "value", "description" : "Value"},
            {"name" : "prc", "description" : "Percentage", "format" : "0.00%"}
            )

    def make_legend(self, columns, orientation="horizontal", location="center", place="below") :
        legend, cmap = [], {}
        for idx, column in enumerate(sorted(columns)) :
            color = self.colors[idx]
            glyph = self.figure.square([1], [1], size=2, color=color, muted_color=color)
            legend.append(LegendItem(label=column, renderers=[glyph]))
            cmap[column] = color

        if self.legend and self.place :
            raise ValueError("Cannot change place of a previous legend for the moment")

        if self.legend :
            self.legend.items = legend
            self.legend.orientation = orientation
            self.legend.location = location

        else :
            legend = Legend(items=legend, orientation=orientation, location=location)
            self.figure.add_layout(legend, place=place)
            self.figure.xaxis.visible = False
            self.figure.yaxis.visible = False
            self._legend = legend

        self._cmap = cmap

    def set_data_source(self, dic, legend=False) :
        df = self.make_data_source(dic)
        if df.empty : raise SourceException("No data source to provide")
        self.source.data = df
        if legend : self.make_legend()

    def make_data_source(self, dic) :
        df = pd.DataFrame([{"name" : name, "value" : value}
            for name, value in dic.items()])

        df['prc'] = df['value'] / df['value'].sum()
        df['angle'] = df['prc'] * 2 * math.pi
       
        if self.cmap : df['color'] = df["name"].map(self.cmap)
        else : df['color'] = self.colors[:len(self.columns)]

        return df
        
    def doubletap(self, event) :
        # https://www.geeksforgeeks.org/check-whether-point-exists-circle-sector-not/
        data = self.source.data
        x, y = event.x, event.y
        x, y = x - 1, y - 1

        point_radius = math.sqrt(x * x + y * y) 
        point_angle = math.atan2(y, x)
        if point_angle < 0 :
            point_angle = (math.pi * 2) + point_angle

        for idx, name in enumerate(data["name"]) :
            start_angle = sum(data["angle"][:idx])
            end_angle = sum(data["angle"][:idx+1])          
            if start_angle <= point_angle <= end_angle and point_radius < PieChart.circle_radius :
                self.emit_signal("doubletap", name)