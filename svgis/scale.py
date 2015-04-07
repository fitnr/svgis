try:
    import numpy as np
except ImportError:
    pass

def geometry(geom, factor=1):
    coordinates = geom['coordinates']

    if geom['type'] == 'MultiPolygon':
        c = [scale_rings(rings, factor) for rings in coordinates]

    elif geom['type'] in ('Polygon', 'MultiLineString'):
        c = scale_rings(coordinates, factor)

    elif geom['type'] in ('MultiPoint', 'LineString'):
        c = scale(coordinates, factor)

    elif geom['type'] == 'Point':
        c = scale(coordinates, factor)

    else:
        raise NotImplementedError("Unknown geometry type")

    return {
        'type': geom['type'],
        'coordinates': c
    }


def scale_rings(rings, factor=1):
    return [scale(ring, factor) for ring in rings]


def scale(coordinates, scalar=1):
    '''Scale a list of coordinates by a scalar. Only use of projected coordinates'''
    try:
        return np.array(coordinates, dtype=float) * scalar
    except NameError:
        if isinstance(coordinates, tuple):
            return (coordinates[0] * scalar, coordinates[1] * scalar)

        return ((x * scalar, y * scalar) for x, y in coordinates)

def feature(feat, factor=1):
    return {
        'properties': feat.get('properties'),
        'geometry': geometry(feat['geometry'], factor),
    }
