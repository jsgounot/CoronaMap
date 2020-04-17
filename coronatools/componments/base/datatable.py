# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-31 14:01:58
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-15 15:21:21

import pandas as pd

from bokeh.models import ColumnDataSource, TableColumn, CustomJS
from bokeh.models import DataTable as BDT

from componments.base.utils import BaseChart
from componments.base.errors import InternalError

class DataTable(BaseChart) :

    """
    We must be aware here that if one change a dataframe value or column (with inplace behavior),
    it's not gonna change the datatable until make_data_source is called,
    or if the whole dataframe is modified. Inheritance of pandas DataFrame is overkill for this.

    Example :
    dt = DataTable()
    df.df = new_df         # Change
    dt.df["name"] = "Bob"  # No change
    df.make_data_source()  # Change
    """

    def __init__(self, * args, columns=[], df=None, dynamic=True, columns_kwargs={}, 
                 keep_selections=False, ** kwargs) :
        

        self._df = pd.DataFrame() if df is None else df
        self._shown_df = None
        self._source = ColumnDataSource() if self.df.empty else ColumnDataSource(self.df)

        columns = columns or self.df.columns
        columns = [TableColumn(field=column, title=column) for column in columns]
        self._dt = BDT(* args, columns=columns, source=self.source, ** kwargs)

        self._dynamic = dynamic
        self._columns_kwargs = columns_kwargs
        self.keep_selections = keep_selections
        self.source.selected.on_change("indices", lambda attr, old, new : self.rows_selection(new))

        # Selection management, necessary when we do a subset (for example a search toolbar)
        self._trigger_selection = True
        self._selected_indices = set()
        self._name_state = True

        super().__init__()

    @property
    def df(self):
        return self._df
    
    @df.setter
    def df(self, df) :
        self._df = df
        self.make_data_source()

    @property
    def shown_df(self) :
        return self._shown_df
    
    @shown_df.setter
    def shown_df(self, shown_df) :
        self._shown_df = shown_df
        self.source.data = shown_df

    @property
    def dynamic(self):
        return self._dynamic

    @property
    def columns_kwargs(self):
        return self._columns_kwargs
    
    @property
    def source(self):
        return self._source
    
    @property
    def dt(self):
        return self._dt
    
    @property
    def trigger_selection(self):
        return self._trigger_selection
    
    @property
    def selected_indices(self):
        return self._selected_indices
    
    def link_input(self, obj, column_name) :
        # Link an input for a query search
        # Not that simple since we need a custom callback to conserve input focus
        # when dataframe change

        if obj.name is None :
            raise InternalError("Please provide a unique name to your widget (as parameter)")

        code = """
        console.log("make focus");
        document.getElementsByName(obj.name)[0].focus();
        console.log("focus done");
        """

        code = CustomJS(args=dict(obj=obj), code=code)
        self.dt.js_on_change("name", code)

        obj.on_change("value_input", lambda attr, old, new : self.subset(column_name, new))             

    def make_data_source(self) :
        if self.dynamic :
            ck = self.columns_kwargs
            columns = [TableColumn(field=column, title=column, ** ck.get(column, {})) 
                       for column in self.df.columns]
            
            self.dt.columns = columns

        self.shown_df = self.df
        
        if not self.keep_selections :
            self.source.selected.indices = []

    def subset(self, colname, search, case_sensitive=False) :
        serie = self.df[colname]
        if not case_sensitive :
            search = search.lower()
            serie = serie.str.lower()

        if search :
            df = self.df[serie.str.contains(search)]
        
        else :
            df = self.df

        self.shown_df = df

        # we set selected indices
        shown_idx = list(df.index)
        select_idx = [idx for idx, main_idx in enumerate(shown_idx) 
                      if main_idx in self.selected_indices]

        self._trigger_selection = False
        self.source.selected.indices = select_idx
        self._trigger_selection = True

        # only way I found to trigger callback
        # maybe fix this in another way
        self._name_state = not self._name_state
        self.dt.name = str(self._name_state)

    def selected_rows(self) :
        return self.df[self.df.index.isin(self.selected_indices)]

    def rows_selection(self, indices) :
        if not self.trigger_selection :
            return

        df = self.shown_df
        df = df.iloc[indices]

        selected = set(df.index)
        unselect = set(self.shown_df.index) - selected

        self._selected_indices |= selected
        self._selected_indices -= unselect

        df = self.selected_rows()
        self.emit_signal("selection", df)