# CoronaMap / Covid-19 map

This repository contains a bokeh application to follow the spread of the Covid-19 virus worldwide.
All the data are fetched from the [CSSEGI repository](https://github.com/CSSEGISandData/COVID-19). 
An instance may be alive [here](http://localhost:5006/coronaboard).

## Features

- Worldmap with daily evolution of the virus propagation worldwide
- Comparison of the data between countries with days shift

## Dependancies

- Python 3.7
- Bokeh
- GeoPandas

## How to

Update local data :

```bash
python fetch_data.py
```

Launch the map :

```bash
bokeh serve --show coronamap.py coronaboad.py
```

You can also ignore `--show` option if you run it to a server.

## Screenshots

![screenshot](https://raw.githubusercontent.com/jsgounot/CoronaTools/master/Screenshots/coronamap.png)

![screenshot](https://raw.githubusercontent.com/jsgounot/CoronaTools/master/Screenshots/coronaboard.png)