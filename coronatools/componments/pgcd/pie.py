# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-29 01:00:32
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-29 03:34:54

from componments.base.utils import ToolTips
from componments.base.pie import PieChart as BPieChart

import layouts.utils as lutils

class PieChart(BPieChart) :

    def __init__(self, pgcd, geocolumn=None, location=None, date=None, columns=None,
            * args, ** kwargs) :
        
        self._pgcd = pgcd

        tooltips = BPieChart.default_tooltips()
        tooltips["value"].format = "0,0"

        super().__init__(* args, tooltips=tooltips, ** kwargs)

        self._geocolumn = geocolumn
        self._location = location
        self._date = date
        self._columns = columns

    @property
    def pgcd(self):
        return self._pgcd
    
    @property
    def geocolumn(self):
        return self._geocolumn
    
    @property
    def location(self):
        return self._location
    
    @property
    def date(self):
        return self._date
    
    @property
    def columns(self):
        return self._columns

    @location.setter
    def location(self, location) :
        self._location = location
        self.set_data_source()

    @date.setter
    def date(self, date) :
        self._date = date
        self.set_data_source()

    @columns.setter
    def columns(self, columns) :
        self._columns = columns
        self.set_data_source()

    @geocolumn.setter
    def geocolumn(self, geocolumn) :
        self._geocolumn = geocolumn

    def make_legend(self, * args, ** kwargs) :
        columns = [lutils.description(column) for column in self.columns]
        super().make_legend(columns=columns)

    def set_data_source(self) :
        if not all((self.geocolumn, self.location, self.columns)) :
            print ("Not all information filled")
            print(f"Geocolumn : {self.geocolumn} - Location : {self.location} - Columns : {self.columns}")
            return

        df = self.pgcd.data_from_day(day=self.date, report=False, fill=True, geocolumn=self.geocolumn)
        df = df[df[self.geocolumn] == self.location]
        
        if df.empty : raise Exception(f"No result found with current pie configuration : {self.geocolumn, self.location, self.day}")
        if len(df) > 1 : raise Exception(f"Multiple results found with current pie configuration : {self.geocolumn, self.location, self.day}")

        dic = list(df[self.columns].T.to_dict().values())[0]
        dic = {lutils.description(column) : value for column, value in dic.items()}
        super().set_data_source(dic)