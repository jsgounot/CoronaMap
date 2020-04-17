# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-29 03:45:15
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-29 14:40:28

from componments.base.stack import StackPlot as BSP
import layouts.utils as lutils

class StackPlot(BSP) :

    ycolumns = ["y1", "y2", "y3"]

    def __init__(self, pgcd, kind, kmapper, * args, geocolumn=None, location=None, 
                 asprc=False, ** kwargs) :
        
        kwargs["x_axis_type"] = "datetime"
        super().__init__("Date", StackPlot.ycolumns, * args, ** kwargs)

        self._pgcd = pgcd
        self._kmapper = kmapper
        self._kind = kind
        self._geocolumn = geocolumn
        self._location = location
        self._asprc = asprc

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
    def asprc(self):
        return self._asprc
    
    @asprc.setter
    def asprc(self, asprc) :
        self._asprc = asprc
        self.set_data_source()

    @property
    def kmapper(self):
        return self._kmapper

    def set_data_source(self, df=None) :
        if df is None : df = self.make_df()
        super().set_data_source(df)

    def make_df(self) :
        if not all((self.geocolumn, self.location)) :
            print ("Not all information filled")
            print(f"Geocolumn : {self.geocolumn} - Location : {self.location}")
            return

        df = self.pgcd.data_from_geocol(self.location, self.geocolumn, fill=True)
        df = df[["Date"] + self.kmapper[self.kind]]
        df.columns = ["Date"] + StackPlot.ycolumns

        if self.asprc :
            df = BSP.df2Prc(df, StackPlot.ycolumns)
        
        return df