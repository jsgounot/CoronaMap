# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-28 16:41:18
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-29 14:03:47

from bokeh.plotting import figure
from bokeh.palettes import Category10_10 as pcolors
from bokeh.models import ColumnDataSource

from componments.base.utils import BaseChart
from componments.base.errors import SourceException

class StackPlot(BaseChart) :
    # Kind of useless but might be improved with newer version of bokeh

    def __init__(self, xcolumn, ycolumns, * args, colors=None, ** kwargs) :       
        colors = colors or pcolors[:len(ycolumns)]

        data = {xcolumn : [], ** {ycolumn : [] for ycolumn in ycolumns}}
        self._source = ColumnDataSource(data)

        self._figure = figure(* args, ** kwargs)
        self._figure.varea_stack(stackers=ycolumns, x=xcolumn, fill_color=colors, source=self.source)

    @property
    def figure(self):
        return self._figure
    
    @property
    def source(self):
        return self._source
    
    @staticmethod
    def df2Prc(df, columns) :
        df[columns] = df[columns].abs()
        sdf = df.copy()

        for column in columns :
            df[column] = sdf[column] / sdf[columns].sum(axis=1)
            df[column] = df[column].fillna(0)

        return df

    def set_data_source(self, df) :
        if df.empty : raise SourceException("No data source to provide")
        self.source.data = df