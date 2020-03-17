# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-14 23:50:19
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-17 14:51:36

import os, glob
import json

from itertools import product

import numpy as np
import pandas as pd
pd.set_option('display.width', 1000)

import geopandas as gpd
from shapely.geometry import Point

bname = os.path.basename
dname = os.path.dirname

def load_geo_data() :
    # https://towardsdatascience.com/a-complete-guide-to-an-interactive-geographical-map-using-python-f4c5197e23e0
    dname = os.path.dirname(os.path.realpath(__file__))
    bname = "Data/Countries/ne_110m_admin_0_countries.shp"
    fname = os.path.join(dname, bname)

    gdf = gpd.read_file(fname)[['ADMIN', 'geometry', "ADM0_A3"]]
    gdf.columns = ['UCountry', 'geometry', "ADM0_A3"]

    # population size : CSV file from here :
    # https://data.worldbank.org/indicator/SP.POP.TOTL

    bname = "Data/API_SP.POP.TOTL_DS2_en_csv_v2_821007.csv"
    fname = os.path.join(dname, bname)
    df = pd.read_csv(fname, skiprows=3)

    def get_last_number(row) :
        row = row.to_dict()
        try : 
            return next(row[str(year)] for year in range(2019, 1960, -1)
                if not np.isnan(row[str(year)]))
        except StopIteration :
            return np.nan

    df["PopSize"] = df.apply(get_last_number, axis=1)
    df = df[["Country Code", "PopSize"]]
    df.columns = ["ADM0_A3", "PopSize"]
    gdf = gdf.merge(df, how='left', on='ADM0_A3')

    return gdf

def scratch_corona_data() :
    fnames = [
    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv",
    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv",
    "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv"]

    def load_data(link) :
        name = link[131:-4]
        print (name)
        df = pd.read_csv(link, sep=",")
        df = pd.melt(df, id_vars=df.columns[:4], value_vars=df.columns[4:], var_name="date", value_name=name)
        return df

    data = [load_data(fname) for fname in fnames]
    df = data.pop(0)

    while data :
        df = df.merge(data.pop(0), on=list(df.columns[:5]))

    return df

def find_count_lon_lat(lon, lat, gdf) :
    point = Point(lon, lat)
    for country, polygone in gdf.items() :
        if polygone.contains(point) :
            return country
    return np.nan

def find_geo_name(row, gdf) :
    lon, lat = row["Long"], row["Lat"]
    return find_count_lon_lat(lon, lat, gdf)

def scrap_and_save() :
    dname = os.path.dirname(os.path.realpath(__file__))
    bname = "Data/corona_data.csv"
    fname = os.path.join(dname, bname)
    
    gdf = load_geo_data()
    cdf = scratch_corona_data()

    fday = pd.to_datetime(cdf['date']).min()
    fun_day = lambda date : dayinf(date, fday)
    cdf["DaysInf"] = pd.to_datetime(cdf['date']).apply(fun_day).dt.days

    gdfd = gdf.set_index("UCountry")["geometry"].to_dict()
    fun_country = lambda row : find_geo_name(row, gdfd)
    cdf["UCountry"] = cdf.apply(fun_country, axis=1)
    
    cdf.to_csv(fname)

def dayinf(date, fday) :
    return date - fday + pd.Timedelta('1 days')

class CoronaData() :

    def __init__(self, head=0) :
        self.jdata = {}
        self.gdf = load_geo_data()

        dname = os.path.dirname(os.path.realpath(__file__))
        bname = "Data/corona_data.csv"
        fname = os.path.join(dname, bname)
        
        self.cdf = pd.read_csv(fname, index_col=0)
        if head : self.cdf = self.cdf.head(head)
        self.update_cdf()

        self.empty_dates = self.make_empty_dates()

    def update_cdf(self) :
        self.cdf = self.cdf.groupby(["UCountry", "date", "DaysInf"])[["Confirmed", "Deaths", "Recovered"]].sum().astype(int).reset_index()

        psize = self.gdf.set_index("UCountry")["PopSize"].to_dict()
        self.cdf["PopSize"] = self.cdf["UCountry"].apply(lambda country : psize[country])

        self.cdf["DRate"] = self.cdf["Deaths"] / self.cdf[["Deaths", "Recovered"]].sum(axis=1)
        self.cdf["DRate"] = self.cdf["DRate"].fillna(0)        

        make_prc_pop = lambda row : row[["Confirmed", "Deaths", "Recovered"]].sum() / row["PopSize"] if not np.isnan(row["PopSize"]) else np.nan
        self.cdf["PrcCont"] = self.cdf.apply(make_prc_pop, axis=1)

    def make_empty_dates(self) :
        return pd.DataFrame([{"date" : date, "count" : 0}
            for date in self.cdf["date"].unique()])

    def df2json(self, day) :
        jdata = self.jdata.get(day, None)
        if jdata : return jdata

        cdf = self.cdf[self.cdf["DaysInf"] == day]
        df = self.gdf[["UCountry", "geometry"]].merge(cdf, on="UCountry", how='left')
        df[["Confirmed", "Deaths", "Recovered"]] = df[["Confirmed", "Deaths", "Recovered"]].fillna(0).astype(int)
        
        # clean data
        df = df[df["UCountry"] != "Antarctica"]
        df = df.drop(["date", "DaysInf"], axis=1)

        jdata = json.loads(df.to_json())
        jdata = json.dumps(jdata)

        self.jdata[day] = jdata
        return jdata

    def df2jsons(self) :
        days = self.cdf["DaysInf"].unique()
        return {int(day) : self.df2json(day)
            for day in days}

    def extract_data_country(self, country, column) :
        sdf = self.cdf[self.cdf["UCountry"] == country]

        sdf = sdf.groupby("date")[column].sum().rename("count").reset_index()
        sdf = pd.concat([sdf, self.empty_dates]).drop_duplicates("date")

        if column in ["PrCont", "DRate"]:
            sdf["count"] = sdf["count"] * 100

        sdf["date"] = pd.to_datetime(sdf["date"], infer_datetime_format=True) 
        sdf = sdf.sort_values("date")

        return sdf["date"], sdf["count"]

if __name__ == "__main__" :
    scrap_and_save()