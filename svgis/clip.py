try:
    from shapely.geometry import shape, mapping
except ImportError:
    pass

def prepare(bbox):
    minx, miny, maxx, maxy = bbox
    bounds = {
        "type": "Polygon",
        "coordinates": [[(minx, miny), (minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny)]]
    }
    try:
        bbox = shape(bounds)

        def func(geometry):
            clipped = bbox.intersection(shape(geometry))
            return mapping(clipped)

    except NameError:
        func = lambda geometry: geometry

    return func

def clip(geometry, bbox):
    '''Clip a geometry to a bounding box. BBOX may be a tuple or a shapely geometry object'''
    try:
        return prepare(bbox)(geometry)

    except NameError:
        return geometry
