# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-26 12:35:34
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-05 12:00:10

from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.events import DoubleTap

from componments.base.utils import BaseChart, ToolTips
from componments.base.errors import SourceException

class DynamicBarPlot(BaseChart) :

    def __init__(self, columnx, columny, ndisplay, * args, tooltips=None, width=.8, 
        kwargs_hovertool={}, data_source={}, ** kwargs) :
        
        tooltips = tooltips or DynamicBarPlot.default_tooltips()
        
        hover = HoverTool(tooltips=tooltips.bokeh_format(), ** kwargs_hovertool)
        kwargs.setdefault("tools", []).append(hover)

        data = data_source or {}
        data.update({"bottom" : [], "left" : [], "right" : []})
        if columnx not in data : data[columnx] = []
        if columny not in data : data[columny] = []

        self._source = ColumnDataSource(data=data)
        self._figure = figure(* args, ** kwargs)
        self.figure.quad(bottom="bottom", top=columny, left="left", right="right",
                         source=self.source, color="#3A5785")

        self.figure.xaxis.visible = False
        self.figure.xgrid.grid_line_color = None
        self.figure.on_event(DoubleTap, self.doubletap)

        self._ndisplay = ndisplay
        self._df = None
        self._width = width
    
        self._columnx = columnx
        self._columny = columny

        super().__init__()

    @staticmethod
    def default_tooltips(columx, columny) :
        return ToolTips(columnx, columny)

    @property
    def figure(self):
        return self._figure
    
    @property
    def source(self):
        return self._source
    
    @property
    def columnx(self):
        return self._columnx
    
    @property
    def columny(self):
        return self._columny
    
    @property
    def ndisplay(self):
        return self._ndisplay
    
    @property
    def df(self):
        return self._df
    
    @property
    def width(self):
        return self._width
    
    @property
    def pad(self):
        return self._width / 2
    
    @df.setter
    def df(self, df) :
        #df = df[[self.columnx, self.columny]]
        df = self.fill_df(df)
        self._df = df
        self.set_data_source()

    @ndisplay.setter
    def ndisplay(self, ndisplay) :
        self._ndisplay = ndisplay
        self.set_data_source()

    @width.setter
    def width(self, width) :
        if width > 1 : raise ValueError("width must be <= 1")
        self._width = width
        self.df = self.fill_df(self.df)
        self.set_data_source()    

    def fill_df(self, df) :
        df["bottom"] = 0
        df["left"] = df["right"] = list(range(len(df)))
        df["left"] = df["left"] - self.pad
        df["right"] = df["right"] + self.pad
        return df

    def set_data_source(self, df=None) :
        df = df or self.df
        df = df.head(self.ndisplay)
        if df.empty : raise ValuError("No data source to provide")
        self.source.data = df

    def doubletap(self, event) :
        df = self.source.data

        close_idx = round(event.x)
        if not close_idx - self.pad <= event.x <= close_idx + self.pad :
            return

        if not 0 <= event.y <= df[self.columny][close_idx] :
            return

        self.emit_signal("doubletap", df[self.columnx][close_idx])