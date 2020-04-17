class ScatterSource() :

    def __init__(self, cdata, lkind, date, c1, c2) :
        # Specific scatter source which plot both current value and old value

        self.cursource = ColumnDataSource(dict(xs=[], ys=[], ratio=[], names=[], kind=[]))
        self.oldsource = ColumnDataSource(dict(xs=[], ys=[], ratio=[], names=[], kind=[]))
        self.linsource = ColumnDataSource(dict(xs=[], ys=[], colors=[]))

        self.cdata = cdata
        self.lkind = lkind
        self.date = date
        
        self.c1 = c1
        self.c2 = c2

    def get_circle_data(self, date, kind) :
        continent = True if self.lkind == "Continent" else False
        data = self.cdata.data_from_day(date, report=True, continent=continent)

        return  {
            "names" : data[self.lkind],
            "xs" : data[self.c1],
            "ys" : data[self.c2],
            "ratio" : data[self.c1] / data[self.c2],
            "kind" : [kind] * len(data)
        }

    def get_line_data(self, date) :
        cols = [self.lkind, self.c1, self.c2]
        continent = True if self.lkind == "Continent" else False

        cdata = self.cdata.data_from_day(date, report=True, continent=continent)[cols]
        pdata = self.cdata.data_from_day(date - 1, report=True, continent=continent)[cols]

        df = cdata.merge(pdata, how="inner", on=self.lkind)
        xvalues = zip(df[self.c1 + "_x"], df[self.c1 + "_y"])
        yvalues = zip(df[self.c2 + "_x"], df[self.c2 + "_y"])

        return {
            "xs" : list(xvalues),
            "ys" : list(yvalues),
            "colors" : ["black"] * len(df)
        }

    def change_lkind(self, lkind) :
        self.lkind = lkind
        self.make_source()

    def set_data_source(self, dic, legend=False)
        data = self.make_data_source(dic)
        if not data : raise ValuError("No data source to provide")
        self.source.data = data
        if legend : self.make_legend()

    """

    def make_source(self) :
        self.linsource.data = self.get_line_data(self.date)
        self.cursource.data = self.get_circle_data(self.date, "Current")
        self.oldsource.data = self.get_circle_data(self.date - 1, "Day before")
       
    """

def scatter_change_date(scattersource, date) :
    scattersource.date = date
    scattersource.make_source()

def scatter_change_axis(scattersource, cname, xaxis) :
    if xaxis : 
        scattersource.c1 = cname
    else : 
        scattersource.c2 = cname
    
    scattersource.make_source()

def scatter_change_axis_behaviour(scatterplot, behaviour) :
    behaviour = ["Independant axis", "Shared axis"][behaviour]
    if behaviour == "Shared axis" : scatterplot.share_axis()
    elif behaviour == "Independant axis" : scatterplot.split_axis()
    else : raise ValueError("Unknown behavior")

def scatter_update(slider, cdata) :
    slider.end = cdata.lastday(report=True)