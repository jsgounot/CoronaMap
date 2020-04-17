# -*- coding: utf-8 -*-
# @Author: jsgounot
# @Date:   2020-04-17 14:22:17
# @Last modified by:   jsgounot
# @Last Modified time: 2020-04-17 14:24:19

import os
rpath = os.path.realpath(__file__)
dname = os.path.dirname

from pycoronadata import PersistantGeoCoronaData

fname = os.path.join(dname(rpath), "data.csv")
pgcd = PersistantGeoCoronaData(fname=fname)
pgcd.update()
pgcd.save()