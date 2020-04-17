# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-28 22:19:49
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-01 01:03:00

import logging
logger = logging.getLogger("coronatools")

from datetime import datetime

from bokeh.models import ColumnDataSource

from componments.base.utils import ToolTips, ToolTip
from componments.base.bar import DynamicBarPlot as BDBP

import layouts.utils as lutils

class DynamicBarPlot(BDBP) :

    def __init__(self, pgcd, geocolumn, column, date, ndisplay, * args, width=.8, ** kwargs) :
        columnx, columny = "Location", "YValue"

        self._pgcd = pgcd
        self._geocolumn = geocolumn
        self._column = column
        self._date = date

        tooltips = lutils.tooltips(self.pgcd_columns())
        tooltips.insert(0, ToolTip("Location"))

        data_source = {column : [] for column in self.pgcd_columns()}
        super().__init__(columnx, columny, ndisplay, * args, width=.8, tooltips=tooltips, data_source=data_source, ** kwargs)      

    @property
    def pgcd(self):
        return self._pgcd
    
    @property
    def geocolumn(self):
        return self._geocolumn
    
    @property
    def column(self):
        return self._column
    
    @property
    def date(self):
        return self._date

    @geocolumn.setter
    def geocolumn(self, geocolumn) :
        self._geocolumn = geocolumn
        self.update()

    @column.setter
    def column(self, column) :
        self._column = column
        self.update()

    @date.setter
    def date(self, date) :
        self._date = date
        self.update()

    def pgcd_columns(self) :
        return [column for column in lutils.ACOLS if column not in ("Date", )]

    def update(self) :
        logger.debug("Launch update DBR")
        df = self.pgcd.data_from_day(day=self.date, report=False, fill=False, geocolumn=self.geocolumn)
        logger.debug("Fetched results")
        df.columns = [{self.geocolumn : "Location"}.get(column, column) for column in df.columns]
        df = df.sort_values(self.column, ascending=False)
        df["YValue"] = df[self.column] 
        logger.debug("Cleaned results")     
        self.df = df