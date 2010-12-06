#!/usr/bin/env python
"""
http://matplotlib.sf.net/matplotlib.pylab.html#-pie for the docstring.
"""

import  pylab as pl
from matplotlib.backends.backend_agg import FigureCanvasAgg

def piechart(big_title,data):
    # create figure
    figwidth = 2.5*len(data)    # inches
    figheight = 3   # inches
    f = pl.figure(None, figsize=(figwidth, figheight))
    pl.rcParams['font.size'] = 8.0
    pl.rcParams['axes.titlesize'] = 12.0
    pl.rcParams['xtick.labelsize'] = 8.0
    pl.rcParams['legend.fontsize'] = 6.0
    Ncols = len(data)
    plotheight = figwidth/Ncols
    H = plotheight/figheight
    W = 1. / Ncols
    bottom = 0
    width = W
    height = H
    i = 0
    for title, values, counts in data:
        left = W*i
        pl.axes([left, bottom, width, height])
        patches = pl.pie(counts,labels=values, autopct='%1.f%%', shadow=True)
        pl.title(title)
        i+=1
    pl.show()
    fl = open(big_title+".png","w")
    canvas = FigureCanvasAgg(f)
    canvas.print_png(fl)
    fl.close()
if __name__ == "__main__":
    data = [ ("test1", ["0","1","2","3"],[23,12,45,56]),
             ("test2", ["0","1","2","3"],[3,12,45,56])]
    piechart("test",data)
