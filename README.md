# CoronoTools / Map and tool to study Covid-19 spread

This repository contains bokeh applications to follow the spread of the Covid-19 virus worldwide.
All the data are fetched from the [CSSEGI repository](https://github.com/CSSEGISandData/COVID-19) using a [dedicated wrapper](https://github.com/jsgounot/PyCoronaData).
An instance may be alive [here](http://jsandbox.info/bokeh/coronatools).

## Features

- Worldmap with daily evolution of the virus propagation worldwide
- Comparison between countries (barplot and metric over time)
- A global view of one country / continement evolution over time

## Dependancies

- Python 3.7
- [Bokeh](https://github.com/bokeh/bokeh)
- [PyCoronaData](https://github.com/jsgounot/PyCoronaData)

## How to

All the different applications can be launche using server files, i.e :

```bash
bokeh serve --allow-websocket-origin=* server/se_worldmap.py
```

## Ressources

This project has been done as a practical tool for my bokeh training. I tried to make most of the tools reusable here, and most of them can be found in directory `conmponments/base`.

## Other websites

- [CSSEGI website](https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6)
- [Coronastats.co](https://coronastats.co/)
- [Covid-19 tracker](https://covid19.nguy.dev/)
- [Coronaboard](https://coronaboard.kr/en/)
- [Worldometers](https://www.worldometers.info/coronavirus/)
- [Arik](https://coronavirus.arik.io/#/)