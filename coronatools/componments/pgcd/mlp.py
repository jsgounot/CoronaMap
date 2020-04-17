# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-29 03:29:44
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-17 19:16:58

import numpy as np
import pandas as pd

from componments.base.utils import ToolTips
from componments.base.mlp import MultiLinesPlot as MLP
from componments.base.errors import SourceException

import layouts.utils as lutils

class MultiLinesPlotScatter(MLP) :

    def __init__(self, pgcd, * args, gcol=None,
        xcol=None, ycol=None, replace_zero=None, ** kwargs) :
        
        self._pgcd = pgcd
        self._gcol = gcol
        self._xcol = xcol
        self._ycol = ycol

        super().__init__(* args, ** kwargs)
        self.ignore = True
        self._replace_zero = replace_zero

    @property
    def pgcd(self):
        return self._pgcd
   
    @property
    def gcol(self) :
        return self._gcol
    
    @gcol.setter
    def gcol(self, gcol) :
        self._gcol = gcol
        self.update(locations=[])

    @property
    def xcol(self) :
        return self._xcol
    
    @xcol.setter
    def xcol(self, xcol) :
        self._xcol = xcol
        self.update()

    @property
    def ycol(self) :
        return self._ycol
    
    @ycol.setter
    def ycol(self, ycol) :
        self._ycol = ycol
        self.update()

    @property
    def replace_zero(self):
        return self._replace_zero
    

    def change_locations(self, locations) :
        tokeep = set(self.df.columns) & set(locations)
        toadd = set(locations) - set(self.df.columns)

        df = self.df
        df = df[tokeep].reset_index()
        for location in toadd :
            sdf = self.data_from_location(location)           

            if df.empty :
                df = sdf
            else :
                df = df.merge(sdf, on=self.xcol, how="outer")

        df = df.set_index(self.xcol)
        if self.replace_zero : df = df.replace(0, self.replace_zero)
        self.df = df

    def data_from_location(self, location, setindex=False) :
        df = self.pgcd.data_from_geocol(location, self.gcol, fill=True, as_datetime=True)

        if df.empty : 
            df = pd.DataFrame(columns=[self.xcol, location])
        else : 
            df = df[[self.xcol, self.ycol]]
            df.columns = [self.xcol, location]
        
        if setindex : df = df.set_index(self.xcol)

        return df

    def update(self, locations=None) :
        locations = list(self.df.columns) if locations is None else locations
        
        if locations :
            df = pd.concat([self.data_from_location(location, setindex=True)
                for location in locations], axis=1)
        else :
            df = pd.DataFrame()     

        try : self.df = df.fillna(0)
        except SourceException : pass

class MultiLinesPlotMapping(MLP) :
       
    def __init__(self, pgcd, kind, kmapper, * args, geocolumn=None, location=None, ** kwargs) :
        tooltips = MLP.default_tooltips()
        tooltips["data_x"].description = "Date"
        tooltips["data_x"].format = "%F"
        tooltips["data_y"].format = "0,0"
        kwargs_hovertool = {"formatters": {'$data_x': 'datetime'}}

        kwargs["x_axis_type"] = "datetime"
        super().__init__(* args, tooltips=tooltips, kwargs_hovertool=kwargs_hovertool, ** kwargs)

        self._pgcd = pgcd
        self._kmapper = kmapper
        self._kind = kind
        self._geocolumn = geocolumn
        self._location = location
        
    @property
    def pgcd(self):
        return self._pgcd
    
    @property
    def kind(self):
        return self._kind
    
    @kind.setter
    def kind(self, kind) :
        self._kind = kind
        self.set_data_source()

    @property
    def geocolumn(self):
        return self._geocolumn
    
    @geocolumn.setter
    def geocolumn(self, geocolumn) :
        self._geocolumn = geocolumn

    @property
    def location(self) :
        return self._location
    
    @location.setter
    def location(self, location) :
        self._location = location
        self.set_data_source()

    @property
    def kmapper(self):
        return self._kmapper
    
    def set_data_source(self, df=None) :
        if df is None : df = self.make_df()
        data = self.make_data_source(df)
        super().set_data_source(data)

    def make_df(self) :
        if not all((self.geocolumn, self.location)) :
            print ("Not all information filled")
            print(f"Geocolumn : {self.geocolumn} - Location : {self.location}")
            return

        value_vars = self.kmapper[self.kind]
        df = self.pgcd.data_from_geocol(self.location, self.geocolumn, fill=True, as_datetime=True)
        df = df.set_index("Date")[value_vars]

        df.columns = [lutils.description(column) for column in df.columns]
        return df