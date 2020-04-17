# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-25 23:11:15
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-01 02:59:15

from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, HoverTool
from bokeh.models.mappers import LogColorMapper, LinearColorMapper
from bokeh.palettes import YlOrRd9 as cpalette
from bokeh.events import DoubleTap

from componments.base.utils import BaseChart

COLOR_MAPPER_NAME = {
    "Log" : "Log scale color mapping",
    "Linear" : "Linear scale color mapping"
}

class WMap(BaseChart) :

    mappers = {
        "Log" : LogColorMapper,
        "Linear" : LinearColorMapper
    }

    def __init__(self, geojson, field, mapper, * args, tooltips=None, kwargs_hovertool={}, ** kwargs) :
        super().__init__()
        self._mapper = mapper
        self._field = field       

        if tooltips :
            hover = HoverTool(tooltips=tooltips.bokeh_format(), ** kwargs_hovertool)
            kwargs.setdefault("tools", []).append(hover)

        self._source = GeoJSONDataSource(geojson=geojson)

        self._figure = figure(* args, ** kwargs)       
        self._patches = self.figure.patches('xs','ys', source=self.source, 
            fill_color={'field' : self.field, 'transform' : self.mapper},
            line_color='black', line_width=0.25, fill_alpha=1)

        lambda_callback_map_dt = lambda event : self.doubletap(event)
        self.figure.on_event(DoubleTap, lambda_callback_map_dt)

        self.figure.xaxis.visible = False
        self.figure.yaxis.visible = False

        self.figure.xgrid.grid_line_color = None
        self.figure.ygrid.grid_line_color = None

    @property
    def figure(self) :
        return self._figure
    
    @property
    def source(self) :
        return self._source
    
    @property
    def patches(self) :
        return self._patches
    
    @property
    def mapper(self) :
        return self._mapper
    
    @mapper.setter
    def mapper(self, value) :
        self._mapper = value
        self.update_patch()

    @property
    def field(self):
        return self._field

    @field.setter
    def field(self, value) :
        self._field = value
        self.update_patch()

    @staticmethod
    def build_mapper(name, low, high, palette=None, ** kwargs) :
        palette = palette or cpalette[::-1]
        return WMap.mappers[name](low=low, high=high, palette=palette, ** kwargs)

    def set_data_source(self, data) :
        if not data : raise ValuError("No data source to provide")
        self.source.geojson = data

    def update_patch(self) :
        self.patches.glyph.fill_color = {'field' : self.field, 
            'transform' : self.mapper}

    def doubletap(self, event) :
        lon, lat = event.x, event.y
        self.emit_signal("doubletap", (lon, lat))

    def update(self) :
        raise NotImplementedError