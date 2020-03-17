# CoronaMap / Covid-19 map

This repository contains a bokeh application to follow the spread of the Covid-19 virus worldwide.
All the data are fetched from the [CSSEGI repository](https://github.com/CSSEGISandData/COVID-19). 

![screenshot](https://raw.githubusercontent.com/jsgounot/CoronaMap/master/screenshot.png)

## Features

- Worldmap with daily evolution of the virus propagation worldwide
- Comparison of the data between countries with days shift

## Dependancies

- Python 3.7
- Bokeh
- GeoPandas

## How to

Update local data :

```python3
python fetch_data.py
```

Launch the map :

```python3
bokeh serve --show coronamap.py
```

