# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-14 23:50:19
# @Last modified by:   jsgounot
# @Last Modified time: 2020-03-20 23:26:18

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

    gdf = gpd.read_file(fname)[['ADMIN', 'geometry', "ADM0_A3", "POP_EST", "CONTINENT"]]
    gdf.columns = ['Country', 'Geometry', "ADM0_A3", "PopSize", "Continent"]

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

def find_country_lon_lat(gdf, lon, lat, guess=None) :
    point = Point(lon, lat)

    if guess in gdf and gdf[guess].contains(point) :
        return guess

    for country, polygone in gdf.items() :
        if polygone.contains(point) :
            return country
    return np.nan

def scrap_and_save() :
    dname = os.path.dirname(os.path.realpath(__file__))
    bname = "Data/corona_data.csv"
    fname = os.path.join(dname, bname)
    
    gdf = load_geo_data()
    cdf = scratch_corona_data()

    # We remove row for which nothing is found
    cdf = cdf[cdf[["Confirmed", "Deaths", "Recovered"]].sum(axis=1) != 0]

    # We confirm country using longitude and latitue
    # since gdf countries does not have the same name than cdf data
    gdfd = gdf.set_index("Country")["Geometry"].to_dict()
    unique_coor = set(zip(cdf["Long"], cdf["Lat"], cdf["Country/Region"]))
    unique_coor = {coor[:2] : find_country_lon_lat(gdfd, * coor)
        for coor in unique_coor}

    # We add the number of active cases
    cdf["Active"] = cdf["Confirmed"] - (cdf["Deaths"] + cdf["Recovered"])

    # We map results and remove previous country column from cdf name
    cdf = cdf.drop(["Country/Region", "Province/State"], axis=1)
    fun_mapping = lambda row : unique_coor[(row["Long"], row["Lat"])]
    cdf["Country"] = cdf.apply(fun_mapping, axis=1)

    # Just to make this clean
    cdf.columns = [column.title() for column in cdf.columns]

    # We aggregate results from the same country and same date
    cols = ["Confirmed", "Active", "Deaths", "Recovered"]
    cdf = cdf.groupby(["Country", "Date"])[cols].sum().astype(int).reset_index()

    cdf.to_csv(fname)
    return cdf

class UpdateError(Exception) :
    pass

class UpdatedData() :

    # Class to manage a file with update management
    # We can update data if at least X hours passed since last update
    update_time = UPDATE_TIME

    def __init__ (self, fname, head=0) :
        self.fname = fname

        self.data = pd.read_csv(self.fname, index_col=0)
        if head : self.cdf = self.cdf.head(head)
        self.update_cdf()

        if TESTING : self.cdf = self.cdf[self.cdf["DaysRep"] <= 10]

    def time_next_update(self) :
        lastmod = datetime.datetime.fromtimestamp(os.path.getmtime(self.fname))
        currtim = datetime.datetime.now()

        diff = currtim - lastmod 
        next_time = CoronaData.update_time - diff

        # we remove second for formating
        hours, remainder = divmod(next_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return "{:02}H:{:02}M".format(int(hours), int(minutes))

    def fake_update(self) :
        # for testing purpose
        print ("FAKE UPDATE")
        self.cdf = pd.read_csv(self.fname, index_col=0)
        self.update_cdf()
        print ("FAKE UPDATE DONE")
        return True

    def check_update(self) :
        if TESTING : return self.fake_update()
        lastmod = datetime.datetime.fromtimestamp(os.path.getmtime(self.fname))
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

class CoronaData(UpdatedData) :

    descriptions = {"Date" : "Date", "CODay" : 'New confirmed', "DEDay" : 'New deaths', "REDay" : 'New recovered',
        "AC10K" : "Actives per 10k", "CO10K" : "Confirmed per 10k", 
        "DE10K" : "Deaths per 10k", "RE10K" : "Recovered per 10k"}

    data_columns = ['Confirmed', 'Active', 'Deaths', 'Recovered', 'DaysRep', 'CODay', 
                    'REDay', 'DEDay', 'DRate', 'PrcCont', 'AC10K', 'CO10K', 'DE10K', 'RE10K']

    def __init__(self, head=0) :
        self.gdf = load_geo_data()

        dname = os.path.dirname(os.path.realpath(__file__))
        bname = "Data/corona_data.csv"
        fname = os.path.join(dname, bname)

        super().__init__(fname, head)

    @property
    def cdf(self):
        return self.data
    
    @cdf.setter
    def cdf(self, cdf) :
        self.data = cdf

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

    def add_daily_cases(self) :
        subdf = self.cdf.copy()
        subdf["DaysRep"] = subdf["DaysRep"] + 1

        columns = ["Confirmed", "Recovered", "Deaths"]
        columns_old = [column + "Old" for column in columns]

        self.cdf = self.cdf.merge(subdf, on=["Country", "DaysRep"], suffixes=("", "Old"), how="left")
        self.cdf[columns_old] = self.cdf[columns_old].fillna(0).astype(int)

        for idx, column in enumerate(columns_old) :
            nname = column[:2].upper() + "Day"
            self.cdf[nname] = self.cdf[columns[idx]] - self.cdf[column]

        self.cdf = self.cdf.drop(["DateOld", "ActiveOld"] + columns_old, axis=1)

    def countries(self, full=False) :
        if full : return sorted(self.gdf["Country"].unique())
        else : return sorted(self.cdf["Country"].unique())

    def continents(self) :
        return sorted(self.gdf["Continent"].unique())

    def days(self) :
        return sorted(self.cdf["Date"].unique())

    def daysRep(self, days) :
        fday = pd.to_datetime(self.cdf['Date']).min()
        return (days - fday + pd.Timedelta('1 days')).dt.days

    def lastday(self, report=False) :
        column = "DaysRep" if report else "Date"
        return self.cdf[column].max()

    def addPopData(self, cdf) :
        columns = ["Confirmed", "Deaths", "Recovered", "Active"]
        cdf["PrcCont"] = cdf[columns[:3]].sum(axis=1) / cdf["PopSize"]

        for column in columns :
            nname = column[:2].upper() + "10K"
            cdf[nname] = cdf[column] * 10000 / cdf["PopSize"]

        return cdf

    def update_cdf(self) :
        # Add other columns
        # Day since first report
        
        self.cdf["DaysRep"] = pd.to_datetime(self.cdf['Date'])
        self.cdf["DaysRep"] = self.daysRep(self.cdf["DaysRep"])

        # We add daily new cases
        self.add_daily_cases()

        # Death rates
        self.cdf["DRate"] = self.cdf["Deaths"] / self.cdf[["Deaths", "Recovered"]].sum(axis=1)
        self.cdf["DRate"] = self.cdf["DRate"].fillna(0)        

        self.cdf["Date"] = pd.to_datetime(self.cdf["Date"], infer_datetime_format=True) 
        self.cdf = self.cdf.sort_values("Date")

    def df2gdf(self, df) :
        if not "Geometry" in df.columns :
            raise ValueError("Geometry must be in df columns")

        df = gpd.GeoDataFrame(df)
        df = df.set_geometry("Geometry")
        return df

    def data_from_day_countries(self, cdf, fill=False, addGeom=False) :
        geocols = ["Country", "Continent", "PopSize"]
        if addGeom : geocols.append("Geometry")
        gdf = self.gdf[geocols]

        if fill :
            gdf["Date"] = next(iter(cdf["Date"]))
            gdf["DaysRep"] = next(iter(cdf["DaysRep"]))

            cdf = gdf.merge(cdf, on=["Country", "Date", "DaysRep"], how="left")
            columns = ["Confirmed", "Active", "Deaths", "Recovered", "CODay", "REDay", "DEDay"]
            cdf[columns] = cdf[columns].fillna(0).astype(int)
            cdf["DRate"] = cdf["DRate"].fillna(0)

        else :
            cdf = gdf.merge(cdf, on=["Country"], how="right")

        return cdf

    def data_from_day_continent(self, cdf, fill=False) :
        mapper_continents = self.gdf.set_index("Country")["Continent"]
        cdf["Continent"] = cdf["Country"].apply(lambda country : mapper_continents[country])
        cdf = cdf.drop("Country", axis=1)
        
        cdf = cdf.groupby(["Continent", "Date", "DaysRep"]).sum().reset_index()
        cdf["DRate"] = cdf["Deaths"] / cdf[["Deaths", "Recovered"]].sum(axis=1)

        gdf = self.gdf.groupby("Continent")["PopSize"].sum()

        if fill :
            gdf = gdf.reset_index()
            gdf["Date"] = next(iter(cdf["Date"]))
            gdf["DaysRep"] = next(iter(cdf["DaysRep"]))
            cdf = gdf.merge(cdf, on=["Continent", "Date", "DaysRep"], how="left")
            
            columns = ["Confirmed", "Active", "Deaths", "Recovered", "CODay", "REDay", "DEDay"]
            cdf[columns] = cdf[columns].fillna(0).astype(int)
            cdf["DRate"] = cdf["DRate"].fillna(0)

        else :
            cdf["PopSize"] = cdf["Continent"].apply(lambda continent : gdf[continent])

        return cdf

    def data_from_day(self, day, report=False, fill=False, addGeom=False, continent=False) :
        column = "DaysRep" if report else "Date"
        cdf = self.cdf[self.cdf[column] == day]
        if continent : cdf = self.data_from_day_continent(cdf, fill=fill)
        else : cdf = self.data_from_day_countries(cdf, fill=fill, addGeom=addGeom)
        return self.addPopData(cdf)

    def data_all_countries(self, fill=False) :
        if fill :
            return pd.concat(
                (self.data_from_day(day, report=True, fill=True)
                for day in range(self.cdf["DaysRep"].max())))

        cdf = self.cdf
        columns = ["Confirmed", "Active", "Deaths", "Recovered", "CODay", "REDay", "DEDay"]
        cdf = cdf.groupby(["Country", "Date", "DaysRep"])[columns].sum().reset_index()
        cdf["DRate"] = cdf["Deaths"] / cdf[["Deaths", "Recovered"]].sum(axis=1)

        gdf = self.gdf[["Country", "Continent", "PopSize"]]
        cdf = gdf.merge(cdf, on="Country", how="right")

        return self.addPopData(cdf)

    def data_from_country(self, country, fill=False, addGeom=False) :
        cdf = self.cdf[self.cdf["Country"] == country]

        geocols = ["Country", "Continent", "PopSize"]
        if addGeom : geocols.append("Geometry")
        gdf = self.gdf[geocols]

        if not fill : 
            cdf = gdf.merge(cdf, on="Country", how="right")
            return self.addPopData(cdf)

        sdf = pd.DataFrame(pd.Series(self.days(), name="Date"))
        sdf["DaysRep"] = self.daysRep(sdf["Date"])
        sdf["Country"] = country

        columns = ["Confirmed", "Active", "Deaths", "Recovered", "CODay", "REDay", "DEDay", "DRate"]
        for column in columns : sdf[column] = 0

        cdf = pd.concat((cdf, sdf))
        cdf = cdf.drop_duplicates("DaysRep").sort_values("DaysRep")

        cdf = gdf.merge(cdf, on="Country", how="right")
        return self.addPopData(cdf)

    def data_world(self) :
        # no need to fill
        return self.data_from_continent(world=True)

    def data_from_continent(self, continent=None, fill=False, world=False) :
        # get data after transform
        if not continent and not world :
            raise ValueError("Continent or world should be filled")

        gdf = self.gdf[["Country", "Continent"]]
        cdf = self.cdf.merge(gdf, on="Country")
        cdf = self.cdf if world else cdf[cdf["Continent"] == continent]
        
        gb = ["Date", "DaysRep"] if world else ["Continent", "Date", "DaysRep"]
        columns = ["Confirmed", "Active", "Deaths", "Recovered", "CODay", "REDay", "DEDay"]
        cdf = cdf.groupby(gb)[columns].sum().reset_index()

        sdf = pd.DataFrame(pd.Series(self.days(), name="Date"))
        sdf["DaysRep"] = self.daysRep(sdf["Date"])
        if not world : sdf["Continent"] = continent

        columns = ["Confirmed", "Active", "Deaths", "Recovered", "CODay", "REDay", "DEDay"]
        for column in columns : sdf[column] = 0

        cdf = pd.concat((cdf, sdf))
        cdf = cdf.drop_duplicates("DaysRep").sort_values("DaysRep")
        
        cdf["DRate"] = cdf["Deaths"] / cdf[["Deaths", "Recovered"]].sum(axis=1)
        cdf["DRate"] = cdf["DRate"].fillna(0)    

        gdf = self.gdf if world else self.gdf[self.gdf["Continent"] == continent]
        cdf["PopSize"] = gdf["PopSize"].sum()
        
        return self.addPopData(cdf)        

if __name__ == "__main__" :
    scrap_and_save()
    c = CoronaData()
    print (c.data_from_day(58, report=True))
    print (c.data_from_day(58, report=True, fill=True))
    print (c.data_from_day(58, report=True, fill=True, addGeom=True))
    print (c.data_from_day(58, report=True, fill=True, continent=True))
    print (c.data_from_day(58, report=True, fill=False, continent=True))
    print (c.data_from_country("China", fill=False))
    print (c.data_from_country("France", fill=True))
    print (c.data_from_continent("Africa", fill=False))
    print (c.data_from_continent("Africa", fill=True))
    print (c.data_from_continent(world=True))