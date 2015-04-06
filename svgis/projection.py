import pyproj


def wgs84():
    return pyproj.Geod(ellps='WGS84')


def tm(x0, y0, y1):
    '''Generate a local transverse mercator projection'''
    proj4 = ('+proj=lcc +lon_0={x0} +lat_1={y1} +lat_2={y0} +lat_0={y1}'
             '+x_0=0 +y_0=0 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0'
             '+units=m +no_defs').format(x0=x0, y0=y0, y1=y1)
    return pyproj.Proj(proj4)
