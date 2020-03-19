# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-14 23:50:19
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-19 19:09:32

import os, glob
import datetime

import numpy as np
import pandas as pd
pd.set_option('display.width', 1000)

import geopandas as gpd
from shapely.geometry import Point

bname = os.path.basename
dname = os.path.dirname

TESTING = False
UPDATE_TIME = datetime.timedelta(hours = 2)

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
        "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv"
    ]

    def load_data(link) :
        name = link[131:-4]
        print ("Fetch from :", name)
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
    return cdf

def dayinf(date, fday) :
    return date - fday + pd.Timedelta('1 days')

class UpdateError(Exception) :
    pass

class CoronaData() :

    descriptions = {"date" : "Date", "CODay" : 'New confirmed', "DEDay" : 'New deaths', "REDay" : 'New recovered',
        "CO10k" : "Confirmed per 10k", "DE10k" : "Deaths per 10k", "RE10k" : "Recovered per 10k"}

    # We can update data if at least X hours passed since last update
    update_time = UPDATE_TIME

    def __init__(self, head=0) :
        self.gdf = load_geo_data()
        self.cdf = pd.read_csv(self.sourcefile, index_col=0)
        head = 1000 if TESTING else head
        if head : self.cdf = self.cdf.head(head)
        self.update_cdf()

    @property
    def sourcefile(self) :
        dname = os.path.dirname(os.path.realpath(__file__))
        bname = "Data/corona_data.csv"
        return os.path.join(dname, bname)

    def time_next_update(self) :
        lastmod = datetime.datetime.fromtimestamp(os.path.getmtime(self.sourcefile))
        currtim = datetime.datetime.now()

        diff = currtim - lastmod 
        next_time = CoronaData.update_time - diff

        # we remove second for formating
        hours, remainder = divmod(next_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return "{:02}H:{:02}M".format(int(hours), int(minutes))

    def full_descriptions(self, astable=False, acols=[]) :
        values = CoronaData.descriptions
        acols = sorted(set(acols) | set(values))
        values = {name : values.get(name, name) for name in acols}
        
        if astable : 
            values = pd.DataFrame([{"Colname" : key, "Description" : value} for key, value in values.items()])
            values = values.sort_values("Colname")
        
        return values

    def description(self, name, default=None) :
        return CoronaData.descriptions.get(name, default)

    def fake_update(self) :
        # for testing purpose
        print ("FAKE UPDATE")
        self.cdf = pd.read_csv(self.sourcefile, index_col=0)
        self.update_cdf()
        print ("FAKE UPDATE DONE")
        return True

    def check_update(self) :
        if TESTING : return self.fake_update()
        lastmod = datetime.datetime.fromtimestamp(os.path.getmtime(self.sourcefile))
        currtim = datetime.datetime.now()

        diff = currtim - lastmod 
        change = diff > CoronaData.update_time

        lastmodh = lastmod.strftime('%Y-%m-%d %H:%M:%S')
        currtimh = currtim.strftime('%Y-%m-%d %H:%M:%S')

        print ("Trying to update ...")
        print ("Current time : %s" %(currtimh))
        print ("Last time since modification : %s" %(lastmodh))
        print ("Time since last update : %s" %(diff))
        print ("Time delta for update : %s" %(CoronaData.update_time))
        print ("Allow update : %s" %(change))

        if not change : return False
        try : return self.make_update()
        except Exception as e : raise UpdateError(e)

    def make_update(self) :      
        # Reload new data
        self.cdf = scrap_and_save()
        self.update_cdf()
        return True

    def launch_update(self) :
        
        try : 
            update_state = self.check_update()
        except UpdateError as e : 
            print ("Update error : %s" %(e))
            return "An unexpected error occured"

        if update_state == True :
            self.emit_signal("update")
            return "Update sucessfull"

        else :
            next_time = self.time_next_update()
            return "Already updated - Time until next update : %s" %(next_time)

    def update_cdf(self) :
        self.cdf = self.cdf.groupby(["UCountry", "date", "DaysInf"])[["Confirmed", "Deaths", "Recovered"]].sum().astype(int).reset_index()

        subdf = self.cdf.copy()
        subdf["DaysInf"] = subdf["DaysInf"] + 1

        self.cdf = self.cdf.merge(subdf, on=["UCountry", "DaysInf"], suffixes=("", "Old"), how="left")
        self.cdf[["ConfirmedOld", "DeathsOld", "RecoveredOld"]] = self.cdf[["ConfirmedOld", "DeathsOld", "RecoveredOld"]].fillna(0).astype(int)

        self.cdf["CODay"] = self.cdf["Confirmed"] - self.cdf["ConfirmedOld"]
        self.cdf["DEDay"] = self.cdf["Deaths"] - self.cdf["DeathsOld"]
        self.cdf["REDay"] = self.cdf["Recovered"] - self.cdf["RecoveredOld"]
        self.cdf = self.cdf.drop(["dateOld", "ConfirmedOld", "DeathsOld", "RecoveredOld"], axis=1)

        psize = self.gdf.set_index("UCountry")["PopSize"].to_dict()
        self.cdf["PopSize"] = self.cdf["UCountry"].apply(lambda country : psize[country])

        self.cdf["DRate"] = self.cdf["Deaths"] / self.cdf[["Deaths", "Recovered"]].sum(axis=1)
        self.cdf["DRate"] = self.cdf["DRate"].fillna(0)        


        self.cdf["PrcCont"] = self.cdf[["Confirmed", "Deaths", "Recovered"]].sum(axis=1) / self.cdf["PopSize"]
        self.cdf["CO10k"] = self.cdf["Confirmed"] * 10000 / self.cdf["PopSize"]
        self.cdf["DE10k"] = self.cdf["Deaths"] * 10000 / self.cdf["PopSize"]
        self.cdf["RE10k"] = self.cdf["Recovered"] * 10000 / self.cdf["PopSize"]

        self.cdf["date"] = pd.to_datetime(self.cdf["date"], infer_datetime_format=True) 
        self.cdf = self.cdf.sort_values("date")

    @property
    def countries(self) :
        return sorted(self.cdf["UCountry"].unique())

if __name__ == "__main__" :
    scrap_and_save()
    #c = CoronaData()