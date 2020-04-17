# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-25 23:11:56
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-16 17:48:18

import numpy as np

from bokeh.layouts import row, column
from bokeh.models import Button, Select, RadioButtonGroup, TextInput

from componments.base.datatable import DataTable
from componments.pgcd.mlp import MultiLinesPlotScatter
from componments.base.layout import LayoutController as BLC
from componments.base.axpanels import PanelAxisTypes as PAT

from layouts import utils as lutils

class LayoutController(BLC) :
    # Otherwise it's too complicated to manage all possible variables :
    # xaxis, yaxis, region, xlog, ylog ...

    def __init__(self, * args, ** kwargs) :
        super().__init__(* args, ** kwargs)
        
        self.componments = {}
        
        # Add trigger
        self.add_on_change_fun("region", self.change_region)
        
        self.add_on_change_fun("xname", self.change_ax_name)
        self.add_on_change_fun("yname", self.change_ax_name)

    @property
    def cpn(self):
        return self.componments
    
    def change_selection(self, df) :
        locations = set(df["Location"])
        self.cpn["mlp"].change_locations(locations)

    def change_ax_name(self, attr, new) :
        if attr == "xname" :
            self.cpn["mlp"].xcol = new
        elif attr == "yname" :
            self.cpn["mlp"].ycol = new 
        else :
            raise ValueError("attr must be xname or yname")

        datatable = self.cpn["datatable"]
        datatable.keep_selections = True
        self.update_dt()
        datatable.keep_selections = False

    def change_region(self, attr, new) :
        self.update_dt()
        self.cpn["mlp"].gcol = new

    def update_dt(self) :
        self.df = self.get_dt_df()
        self.cpn["datatable"].df = self.df

    def get_dt_df(self) :
        # Add location to data table
        df = self.pgcd.gdf[self.region].drop_duplicates().to_frame()
        df.columns = ["Location"]

        # Add xname and rnam
        cdf = self.pgcd.data_from_day(geocolumn=self.region, fill=True)

        cdf = cdf[[self.region, self.xname, self.yname]]
        cdf.columns = ["Location", self.xname, self.yname]

        df = df.merge(cdf, on="Location", how='left').fillna(0)
        df["Slide"] = "0"

        df = df.sort_values("Location")
        df = df.reset_index(drop=True)

        # df = df.astype(str)
        
        return df

    def table_search(self, search) :
        self.cpn["datatable"].subset("Location", search)

# ---------------------------------------------------------------------------

def construct(pgcd, controller=None) :
    regions = ["Continent", "Country"]
    
    default_idx = 0
    default_reg = regions[default_idx]
    default_col = ["Date", "Confirmed"]
    default_type = ["Linear", "Linear"]

    lc_data = {"pgcd" : pgcd, "region" : default_reg, "xname" : default_col[0], "yname" : default_col[1],
               "xtype" : default_type[0], "ytype" : default_type[1], "selections" : [], "df" : None}

    lc = LayoutController(** lc_data)
    
    axtype1 = PAT.axis_type(title="Linear scale", x="datetime", y="linear")
    axtype2 = PAT.axis_type(title="Log scale", x="datetime", y="log", kwargs={"replace_zero":np.nan})
    
    tooltips = MultiLinesPlotScatter.default_tooltips()
    tooltips["data_x"].description = "Date"
    tooltips["data_x"].format = "%F"
    kwargs_hovertool = {"formatters": {'$data_x': 'datetime'}}

    mlp = PAT(MultiLinesPlotScatter, (axtype1, axtype2),
              pgcd, gcol=default_reg, xcol=default_col[0], ycol=default_col[1],
              aspect_ratio=2, sizing_mode="scale_both", tools=["reset"],
              tooltips=tooltips, kwargs_hovertool=kwargs_hovertool)

    lc.cpn["mlp"] = mlp

    # Select for MLP
    options = [column for column in lutils.columns_description() if column not in ["Date"]]
    ysc = Select(title="Y axis", options=options, value=default_col[1], sizing_mode="stretch_width")

    rdesc_column = lambda column : lutils.description(column, reverse=True)
    lc.link_on_change("yname", ysc, postfun=rdesc_column)

    # DataTable
    formatter = {acol : {"formatter" : aformat} for acol, aformat in lutils.dic_formatter().items()}
    dt = DataTable(width=100, height=200, selectable="checkbox", columns_kwargs=formatter, sizing_mode="stretch_width")

    lc.cpn["datatable"] = dt
    dt.add_receiver("selection", lc.change_selection)

    # Search input for datatable
    ti = TextInput(name="datatableinput", placeholder="Search a country or region ...", sizing_mode="stretch_width")
    dt.link_input(ti, "Location")

    # Region toggle
    funregion = lambda idx :regions[idx]
    rbg = RadioButtonGroup(labels=regions, active=default_idx, sizing_mode="stretch_width")
    lc.link_on_change("region", rbg, "active", postfun=funregion)

    # Buttons for DataTable
    button_auto = Button(label="Auto overlay", button_type="success", sizing_mode="stretch_width")
    #cbba = lambda : distplots_autooveraly(distplots, cdata)
    #button_auto.on_click(cbba) 

    button_reset = Button(label="Reset", button_type="warning", sizing_mode="stretch_width")

    lc.update_dt()
    lc.yname = "Deaths"

    return column(
            mlp.figure,
            row(ysc, sizing_mode="stretch_width"),
            rbg,
            ti,
            dt.dt,
            #row(button_reset, button_auto, sizing_mode="stretch_both"),
            sizing_mode="stretch_both")