# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-03-26 11:45:36
# @Last modified by:   jsgounot
# @Last Modified time: 2020-05-03 18:15:19

from bokeh.models import DateFormatter, NumberFormatter

from componments.base.utils import ToolTips, ToolTip

ACOLS = {
    "Date" : None, "Confirmed" : '0,0', "Active" : "0,0", "Deaths" : '0,0', "Recovered" : '0,0', "LRate" : '0%', 
    "CODay" : '0,0', "DEDay" : '0,0', "REDay" : '0,0', "PopSize" : '0,0', "PrcCont" : '0.000%',
    "AC10K" : "0.000", "CO10K" : '0.000', "DE10K" : '0.000', "RE10K" : '0.000'
    }

DESCRIPTIONS = {"LRate" : "Lethality rate", "CODay" : "Daily confirmed", "DEDay" : "Daily deaths",
        "REDay" : "Daily recovered", "PopSize" : "Population size", "PrcCont" : "Contaminated population (%)",
        "AC10K" : "Active per 10K", "CO10K" : "Confirmed per 10K", "DE10K" : "Deaths per 10K", "RE10K" : "Recovered per 10K"
        }

def reverse_mapping(mapper, name) :
    mapper = {value : key for key, value in mapper.items()}
    return mapper.get(name, name)

def description(name, reverse=False) :
    mapper = DESCRIPTIONS
    if reverse : mapper = {value : key for key, value in mapper.items()}
    return mapper.get(name, name)

def columns_description() :
    return (description(column) for column in ACOLS)

def hoover_format() :  
    for acol, formating in ACOLS.items() :
        if not formating : yield (description(acol, acol), "@" + acol)
        else : yield (description(acol), '@%s{%s}' %(acol, formating))

def tooltips(columns=None) :
    columns = columns or list(ACOLS)
    tooltips = ToolTips()
    for column in columns :
        formating = ACOLS[column]
        desc = description(column)
        if formating : tooltips.append(ToolTip(column, desc, formating))
        else : tooltips.append(ToolTip(column, desc))
    return tooltips

def dic_formatter() :
    return {acol : formatter(acol) for acol in ACOLS}

def formatter(acol) :
    value = ACOLS[acol]
    if acol == "Date" : return DateFormatter()
    return NumberFormatter(format=value)

def lambda_set(attribute, value) :
    attribute = value