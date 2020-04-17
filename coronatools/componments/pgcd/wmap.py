# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-30 01:48:52
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-01 01:45:22

import json
from functools import lru_cache

from shapely.geometry import Point

from componments.base.wmap import WMap as BWMap
from componments.base.utils import ToolTip

class WMap(BWMap) :

    def __init__(self, pgcd, date, field, mkind="Log", tooltips=None, * args, ** kwargs) :
        # Low resolution map, to change if light=False in jdata_day function
        self._gdf = pgcd.load_gdf(default_detail=110)[["Country", "geometry"]]

        # pgcd attributes
        self._pgcd = pgcd
        self._date = date
        self._mkind = mkind

        tooltips = tooltips or ToolTips()
        tooltips.insert(0, ToolTip("Country", "Country"))
 
        # we make the mapper
        low = pgcd.cdf[field].min()
        high = pgcd.cdf[field].max()
        mapper = BWMap.build_mapper(mkind, low, high)

        geojson = self.jdata()
        super().__init__(geojson, field, mapper, * args, tooltips=tooltips, ** kwargs)

    @property
    def pgcd(self):
    	return self._pgcd

    @property
    def gdf(self):
        return self._gdf
    
    @property
    def date(self):
    	return self._date
    
    @date.setter
    def date(self, date) :
    	self._date = date
    	self.set_data_source()
    	self._figure.title.text = 'Coronavirus map : Day ' + str(date)

    @property
    def mkind(self):
    	return self._mkind
    
    @mkind.setter
    def mkind(self, mkind) :
    	self._mkind = mkind
    	self.set_mapper()

    @lru_cache(maxsize=50)
    def jdata_day(self, date) :
        # Lower lru cache maxsize for memory reduction

        df = self.pgcd.data_from_day(self.date, report=False, fill=True)
        df = self.pgcd.df2gdf(df, "Country", light=True)
        df = df[df["geometry"] != None]

        # clean data
        df = df[df["Country"] != "Antarctica"]
        df = df.drop("RepDays", axis=1)
        df["Date"] = df["Date"].astype(str)

        jdata = json.loads(df.to_json())
        return json.dumps(jdata)

    def jdata(self) :
        return self.jdata_day(self.date)

    def set_data_source(self) :
        super().set_data_source(self.jdata())

    def set_mapper(self) :
        low = self.pgcd.cdf[self.field].min()
        high = self.pgcd.cdf[self.field].max()
        self.mapper = WMap.build_mapper(self.mkind, low, high)

    def doubletap(self, event) :
        point = Point(event.x, event.y)
        gdf = self.gdf[self.gdf["geometry"].apply(lambda polygone : polygone.contains(point))]
        if len(gdf) == 1 : self.emit_signal("doubletap", list(gdf["Country"])[0])